import json, re, os, time
from pathlib import Path
import requests
import xml.etree.ElementTree as ET

OPS_TOKEN_URL = "https://ops.epo.org/3.2/auth/accesstoken"
OPS_DESC_URL = "https://ops.epo.org/3.2/rest-services/published-data/publication/docdb/{docdb}/description"

def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def get_token():
    r = requests.post(
        OPS_TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "client_credentials"},
        auth=(os.environ["OPS_KEY"], os.environ["OPS_SECRET"]),
    )
    r.raise_for_status()
    return r.json()["access_token"]

def fetch_xml(docdb, token):
    r = requests.get(
        OPS_DESC_URL.format(docdb=docdb),
        headers={"Authorization": f"Bearer {token}"},
    )
    r.raise_for_status()
    return r.text

def extract_paragraphs(xml_text):
    root = ET.fromstring(xml_text)
    desc = root.find(".//{*}description")
    if desc is None:
        return "", []
    lang = desc.attrib.get("lang", "")
    ps = []
    for p in desc.findall(".//{*}p"):
        t = "".join(p.itertext()).strip()
        if t:
            ps.append(t)
    return lang, ps

def main():
    rows = []
    with open("artifacts/claims_representation_v3.jsonl", "r") as f:
        for line in f:
            rows.append(json.loads(line))

    # 真正只選 US.A
    us_rows = [
        r for r in rows
        if re.match(r"^US\.[0-9]+\.A", r.get("selected_publication",""))
    ]

    print(f"[info] US-A rows = {len(us_rows)}")

    Path("cache/ops_description/US_A").mkdir(parents=True, exist_ok=True)

    token = get_token()

    with open("artifacts/spec_fetch_us_a_v2.jsonl","w") as flog, \
         open("artifacts/chunks_us_a_spec_v2.jsonl","w") as fch:

        for r in us_rows:
            docdb = r["selected_publication"]
            try:
                xml = fetch_xml(docdb, token)
                lang, ps = extract_paragraphs(xml)

                for p in ps:
                    rec = {
                        "selected_publication": docdb,
                        "jurisdiction": "US",
                        "language": lang,
                        "text": p,
                        "created_at": now_iso()
                    }
                    fch.write(json.dumps(rec) + "\n")

                flog.write(json.dumps({
                    "spec_selected_publication": docdb,
                    "spec_status": "SPEC_OK"
                }) + "\n")

            except Exception as e:
                flog.write(json.dumps({
                    "spec_selected_publication": docdb,
                    "spec_status": "SPEC_ERROR",
                    "error": str(e)
                }) + "\n")

    print("[done]")

if __name__ == "__main__":
    main()
