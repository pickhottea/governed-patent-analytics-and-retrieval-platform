import os, json, time, re, argparse
from pathlib import Path
import requests
import xml.etree.ElementTree as ET

OPS_TOKEN_URL = "https://ops.epo.org/3.2/auth/accesstoken"
OPS_DESC_URL  = "https://ops.epo.org/3.2/rest-services/published-data/publication/docdb/{docdb}/description"

def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def get_token(key: str, secret: str, timeout: int = 30) -> str:
    r = requests.post(
        OPS_TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "client_credentials"},
        auth=(key, secret),
        timeout=timeout,
    )
    r.raise_for_status()
    return r.json()["access_token"]

def fetch_xml(docdb: str, token: str, timeout: int = 60) -> str:
    r = requests.get(
        OPS_DESC_URL.format(docdb=docdb),
        headers={"Authorization": f"Bearer {token}", "Accept": "application/xml"},
        timeout=timeout,
    )
    r.raise_for_status()
    return r.text

def extract_paragraphs(xml_text: str):
    root = ET.fromstring(xml_text)
    desc = root.find(".//{*}description")
    if desc is None:
        return "", []
    lang = desc.attrib.get("lang", "") or ""
    ps = []
    for p in desc.findall(".//{*}p"):
        t = "".join(p.itertext()).strip()
        if t:
            ps.append(t)
    return lang, ps

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lane_tsv", default="artifacts/ep_missing_lane_v1.tsv")
    ap.add_argument("--cache_dir", default="cache/ops_description/EP_B1")
    ap.add_argument("--out_log", default="artifacts/spec_fetch_ep_b1_v2.jsonl")
    ap.add_argument("--out_chunks", default="artifacts/chunks_ep_b1_spec_v2.jsonl")
    args = ap.parse_args()

    key = os.environ.get("OPS_KEY")
    secret = os.environ.get("OPS_SECRET")
    if not key or not secret:
        raise SystemExit("Missing OPS_KEY / OPS_SECRET")

    token = get_token(key, secret)

    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    ok = 0
    with open(args.lane_tsv, "r", encoding="utf-8") as f_in, \
         open(args.out_log, "w", encoding="utf-8") as f_log, \
         open(args.out_chunks, "w", encoding="utf-8") as f_ch:

        for line in f_in:
            line = line.strip()
            if not line:
                continue
            family_id, asset_id, docdb, seed_pub = line.split("\t")[:4]

            if not re.match(r"^EP\.[0-9]+\.B1$", docdb):
                continue

            xml_path = cache_dir / (docdb.replace(".", "_") + ".xml")

            try:
                if xml_path.exists():
                    xml = xml_path.read_text(encoding="utf-8")
                    status = "SPEC_OK(CACHE)"
                else:
                    xml = fetch_xml(docdb, token)
                    xml_path.write_text(xml, encoding="utf-8")
                    status = "SPEC_OK"

                lang, ps = extract_paragraphs(xml)

                for p in ps:
                    rec = {
                        "chunk_type": "spec_fulltext",
                        "family_id": family_id,
                        "asset_id": asset_id,
                        "selected_publication": docdb,
                        "jurisdiction": "EP",
                        "kind": "B1",
                        "language": lang,
                        "spec_source": "OPS",
                        "spec_raw_xml_path": str(xml_path),
                        "seed_publication_number": seed_pub,
                        "text": p,
                        "created_at": now_iso(),
                    }
                    f_ch.write(json.dumps(rec, ensure_ascii=False) + "\n")

                f_log.write(json.dumps({
                    "family_id": family_id,
                    "asset_id": asset_id,
                    "spec_selected_publication": docdb,
                    "spec_status": status,
                    "created_at": now_iso(),
                }) + "\n")

                ok += 1

            except Exception as e:
                f_log.write(json.dumps({
                    "family_id": family_id,
                    "asset_id": asset_id,
                    "spec_selected_publication": docdb,
                    "spec_status": "SPEC_ERROR",
                    "error": str(e),
                    "created_at": now_iso(),
                }) + "\n")

    print(f"[done] EP.B1 ok_rows={ok}")

if __name__ == "__main__":
    main()
