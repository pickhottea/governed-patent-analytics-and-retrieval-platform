#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, os, re, time, hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple
import requests
import xml.etree.ElementTree as ET


OPS_TOKEN_URL = "https://ops.epo.org/3.2/auth/accesstoken"
OPS_DESC_URL = "https://ops.epo.org/3.2/rest-services/published-data/publication/docdb/{docdb}/description"


# ---------------------------
# Utility
# ---------------------------

def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()

def docdb_to_fname(docdb: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", docdb.strip())


# ---------------------------
# OPS
# ---------------------------

def get_ops_token(key: str, secret: str, timeout: int = 30) -> str:
    r = requests.post(
        OPS_TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "client_credentials"},
        auth=(key, secret),
        timeout=timeout,
    )
    r.raise_for_status()
    return r.json()["access_token"]

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


# ---------------------------
# Google fallback
# ---------------------------
def _us_insert_zero_variant(pub: str) -> str | None:
    """
    Google sometimes uses zero-padded US publication numbers:
    US2020123456A1 -> US20200123456A1
    """
    m = re.match(r"^(US)(\d{4})(\d+)([A-Z]\d?)$", pub.replace(".", ""))
    if not m:
        return None

    cc, year, rest, kind = m.groups()

    # pad rest to at least 7 digits
    if len(rest) < 7:
        rest = rest.zfill(7)

    return f"{cc}{year}{rest}{kind}"


def fetch_google_description(pub: str, timeout: int = 30):

    base_pub = pub.replace(".", "").upper()
    variants = [base_pub]

    alt0 = _us_insert_zero_variant(base_pub)
    if alt0 and alt0 != base_pub:
        variants.append(alt0)

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html",
        "Accept-Language": "en,en-US;q=0.9",
    }

    for v in variants:

        url = f"https://patents.google.com/patent/{v}/en"

        try:
            r = requests.get(url, headers=headers, timeout=timeout)
        except Exception as e:
            continue

        if r.status_code != 200:
            continue

        html = r.text

        # remove claims section
        html = re.sub(
            r"<section[^>]*itemprop=['\"]claims['\"][\s\S]*?</section>",
            " ",
            html,
            flags=re.I,
        )

        # try description
        m = re.search(
            r"(<section[^>]*itemprop=['\"]description['\"][\s\S]*?</section>)",
            html,
            flags=re.I,
        )

        if m:
            block = m.group(1)
        else:
            m2 = re.search(r"<body[\s\S]*?</body>", html, flags=re.I)
            if not m2:
                continue
            block = m2.group(0)

        text = re.sub(r"<script[\s\S]*?</script>", " ", block, flags=re.I)
        text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        if len(text) < 1500:
            continue

        paragraphs = [p.strip() for p in re.split(r"\.\s+", text) if len(p.strip()) > 60]

        if paragraphs:
            return "EN", paragraphs, "GOOGLE_OK"

    return "", [], "GOOGLE_FAILED_ALL_VARIANTS"



# ---------------------------
# Chunking
# ---------------------------

def chunk_by_paragraphs(paragraphs: List[str], max_chars=4500, overlap_chars=800):
    chunks = []
    meta = []

    buf = []
    buf_len = 0

    def flush():
        nonlocal buf, buf_len
        if not buf:
            return
        text = "\n".join(buf).strip()
        if text:
            chunks.append(text)
            meta.append({"para_count": len(buf)})

        if overlap_chars <= 0:
            buf, buf_len = [], 0
            return

        keep = []
        keep_len = 0
        for p in reversed(buf):
            if keep_len + len(p) > overlap_chars and keep:
                break
            keep.append(p)
            keep_len += len(p)
        keep = list(reversed(keep))
        buf = keep
        buf_len = sum(len(x) for x in keep)

    for p in paragraphs:
        plen = len(p)
        if buf_len + plen > max_chars and buf:
            flush()
        buf.append(p)
        buf_len += plen

    flush()
    return list(zip(chunks, meta))


# ---------------------------
# Main
# ---------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_path", default="artifacts/claims_representation_v3.jsonl")
    ap.add_argument("--out_chunks", default="artifacts/chunks_us_spec_v2.jsonl")
    ap.add_argument("--out_log", default="artifacts/spec_fetch_us_spec_v2.jsonl")
    ap.add_argument("--max_chars", type=int, default=4500)
    ap.add_argument("--overlap_chars", type=int, default=800)
    args = ap.parse_args()

    key = os.environ.get("OPS_KEY")
    secret = os.environ.get("OPS_SECRET")
    if not key or not secret:
        raise SystemExit("Missing OPS_KEY / OPS_SECRET")

    rows = []
    with open(args.in_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))

    us_rows = [
        r for r in rows
        if re.match(r"^US\.[0-9]+\.A", str(r.get("selected_publication","")))
    ]

    print(f"[info] US-A rows = {len(us_rows)}")

    token = get_ops_token(key, secret)

    with open(args.out_log, "w", encoding="utf-8") as flog, \
         open(args.out_chunks, "w", encoding="utf-8") as fch:

        for r in us_rows:

            family_id = r.get("family_id")
            asset_id = r.get("asset_id")
            pub = r.get("selected_publication")
            selected_source = r.get("selected_source")
            governance_flags = r.get("governance_flags") or []

            spec_source = "OPS"
            google_status = None
            spec_google_text_path = None
            spec_raw_xml_path = None
            paragraphs = []
            lang = "UNK"
            status = "SPEC_OK"

            try:
                xml_text = fetch_description_xml(pub, token)
                lang, paragraphs = extract_description_paragraphs(xml_text)

                if not paragraphs:
                    raise ValueError("OPS_EMPTY")

                spec_raw_xml_path = "OPS_INLINE"

            except Exception:
                # fallback
                spec_source = "GOOGLE"
                lang, paragraphs, google_status = fetch_google_description(pub)

                if not paragraphs:
                    status = "SPEC_FALLBACK_FAILED"

                else:
                    cache_dir = Path("cache/google_spec/US")
                    cache_dir.mkdir(parents=True, exist_ok=True)
                    spec_google_text_path = str(cache_dir / f"{docdb_to_fname(pub)}.txt")
                    Path(spec_google_text_path).write_text(
                        "\n".join(paragraphs),
                        encoding="utf-8"
                    )

            if paragraphs:

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
                        "jurisdiction": "US",
                        "language": lang,
                        "selected_source": selected_source,
                        "governance_flags": governance_flags,
                        "spec_source": spec_source,
                        "spec_raw_xml_path": spec_raw_xml_path,
                        "spec_google_text_path": spec_google_text_path,
                        "google_status": google_status,
                        **m,
                        "text": text,
                        "created_at": now_iso(),
                    }

                    fch.write(json.dumps(rec, ensure_ascii=False) + "\n")

            flog.write(json.dumps({
                "family_id": family_id,
                "asset_id": asset_id,
                "spec_selected_publication": pub,
                "spec_source": spec_source,
                "spec_status": status,
                "google_status": google_status,
                "created_at": now_iso(),
            }, ensure_ascii=False) + "\n")

    print("[done]")


if __name__ == "__main__":
    main()
