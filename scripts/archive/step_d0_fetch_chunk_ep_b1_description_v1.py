python - <<'PY'
import argparse, json, os, re, time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Dict, Any, Tuple
import requests
import xml.etree.ElementTree as ET
import hashlib

OPS_TOKEN_URL = "https://ops.epo.org/3.2/auth/accesstoken"
OPS_DESC_URL = "https://ops.epo.org/3.2/rest-services/published-data/publication/docdb/{docdb}/description"

def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()

def docdb_to_fname(docdb: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", docdb.strip())

def get_ops_token(key: str, secret: str, timeout: int = 30) -> str:
    r = requests.post(
        OPS_TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "client_credentials"},
        auth=(key, secret),
        timeout=timeout,
    )
    r.raise_for_status()
    j = r.json()
    return j["access_token"]

def fetch_description_xml(docdb: str, token: str, timeout: int = 60) -> str:
    url = OPS_DESC_URL.format(docdb=docdb)
    r = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/xml"},
        timeout=timeout,
    )
    r.raise_for_status()
    return r.text

def extract_description_paragraphs(xml_text: str) -> Tuple[str, List[str]]:
    """
    Return (lang, paragraphs). OPS fulltext description typically:
    <description lang="EN"><p>...</p>...</description>
    We keep paragraph text as-is (strip only ends).
    """
    root = ET.fromstring(xml_text)

    # Find first <description ...> regardless of namespace
    desc = root.find(".//{*}description")
    if desc is None:
        return ("", [])

    lang = desc.attrib.get("lang", "") or desc.attrib.get("{http://www.w3.org/XML/1998/namespace}lang", "") or ""
    ps = []
    for p in desc.findall(".//{*}p"):
        t = "".join(p.itertext()).strip()
        if t:
            ps.append(t)
    return (lang, ps)

_parano_ref = re.compile(r"\[(\d{4})\]")  # [0001]

def paragraph_refs(text: str) -> List[str]:
    return _parano_ref.findall(text)

def chunk_by_paragraphs(paragraphs: List[str], max_chars: int = 4500, overlap_chars: int = 800) -> List[Tuple[str, Dict[str, Any]]]:
    """
    超極簡 chunk：用字元長度近似 token。
    - max_chars 約略對應 700~900 tokens（視英文密度）
    - 以段落為邊界拼接，不在段落中間切
    """
    chunks: List[str] = []
    meta: List[Dict[str, Any]] = []

    buf: List[str] = []
    buf_len = 0

    def flush():
        nonlocal buf, buf_len
        if not buf:
            return
        text = "\n".join(buf).strip()
        if text:
            chunks.append(text)

            # 嘗試抓段落編號範圍（如 [0001]...[0004]）
            refs = []
            for b in buf:
                refs += paragraph_refs(b)
            pr = None
            if refs:
                pr = f"[{refs[0]}]-[{refs[-1]}]"
            meta.append({"paragraph_range": pr, "para_count": len(buf)})

        # overlap：保留尾端 overlap_chars 的內容（按段落回退）
        if overlap_chars <= 0:
            buf, buf_len = [], 0
            return
        keep: List[str] = []
        keep_len = 0
        for p in reversed(buf):
            if keep_len + len(p) + 1 > overlap_chars and keep:
                break
            keep.append(p)
            keep_len += len(p) + 1
        keep = list(reversed(keep))
        buf, buf_len = keep, sum(len(x) + 1 for x in keep)

    for p in paragraphs:
        plen = len(p) + 1
        if buf_len + plen > max_chars and buf:
            flush()
        buf.append(p)
        buf_len += plen

    flush()
    return list(zip(chunks, meta))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_path", default="artifacts/claims_representation_v3.jsonl")
    ap.add_argument("--out_chunks", default="artifacts/chunks_ep_b1_spec_v1.jsonl")
    ap.add_argument("--out_log", default="artifacts/spec_fetch_ep_b1_v1.jsonl")
    ap.add_argument("--cache_dir", default="cache/ops_description/EP_B1")
    ap.add_argument("--only_wo", action="store_true", default=True)
    ap.add_argument("--max_chars", type=int, default=4500)
    ap.add_argument("--overlap_chars", type=int, default=800)
    args = ap.parse_args()

    key = os.environ.get("OPS_KEY")
    secret = os.environ.get("OPS_SECRET")
    if not key or not secret:
        raise SystemExit("Missing OPS_KEY / OPS_SECRET env vars")

    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    # load rows
    rows: List[Dict[str, Any]] = []
    with open(args.in_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    # filter WO pubs
    wo_rows = [r for r in rows if re.match(r"^EP\.[0-9]+\.A", str(r.get("selected_publication","")))]
    print(f"[info] EP-B1 rows = {len(wo_rows)}")

    token = get_ops_token(key, secret)

    out_log = Path(args.out_log)
    out_chunks = Path(args.out_chunks)
    out_log.parent.mkdir(parents=True, exist_ok=True)

    with out_log.open("w", encoding="utf-8") as flog, out_chunks.open("w", encoding="utf-8") as fch:
        ok = 0
        for r in wo_rows:
            family_id = r.get("family_id")
            asset_id = r.get("asset_id")
            pub = r.get("selected_publication")
            selected_source = r.get("selected_source")
            governance_flags = r.get("governance_flags") or []

            docdb = pub  # already docdb style (WO.2024....A1)
            fname = docdb_to_fname(docdb) + ".xml"
            xml_path = cache_dir / fname

            status = "SPEC_OK"
            err = None

            try:
                if not xml_path.exists():
                    xml_text = fetch_description_xml(docdb, token)
                    xml_path.write_text(xml_text, encoding="utf-8")
                else:
                    xml_text = xml_path.read_text(encoding="utf-8")

                lang, paragraphs = extract_description_paragraphs(xml_text)
                if not paragraphs:
                    status = "SPEC_PARSE_EMPTY"
                else:
                    # chunk
                    chunked = chunk_by_paragraphs(
                        paragraphs,
                        max_chars=args.max_chars,
                        overlap_chars=args.overlap_chars,
                    )
                    for i, (text, m) in enumerate(chunked, start=1):
                        chunk_id = sha1(f"spec|{pub}|{i}|{sha1(text)}")
                        rec = {
                            "chunk_id": chunk_id,
                            "chunk_type": "spec_fulltext",
                            "family_id": family_id,
                            "asset_id": asset_id,
                            "selected_publication": pub,
                            "jurisdiction": "WO",
                            "language": lang or "UNK",
                            "selected_source": selected_source,
                            "governance_flags": governance_flags,
                            "spec_source": "OPS",
                            "spec_raw_xml_path": str(xml_path),
                            **m,
                            "text": text,
                            "created_at": now_iso(),
                        }
                        fch.write(json.dumps(rec, ensure_ascii=False) + "\n")

                ok += 1

            except requests.HTTPError as ex:
                status = "SPEC_HTTP_ERROR"
                err = str(ex)
            except Exception as ex:
                status = "SPEC_ERROR"
                err = str(ex)

            flog.write(json.dumps({
                "family_id": family_id,
                "asset_id": asset_id,
                "spec_selected_publication": pub,
                "spec_source": "OPS",
                "spec_raw_xml_path": str(xml_path) if xml_path.exists() else None,
                "spec_status": status,
                "error": err,
                "created_at": now_iso(),
            }, ensure_ascii=False) + "\n")

        print(f"[done] wrote: {out_log} / {out_chunks} | ok_rows={ok}")

if __name__ == "__main__":
    main()
PY