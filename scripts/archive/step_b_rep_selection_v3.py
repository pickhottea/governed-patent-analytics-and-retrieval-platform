#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Step B — Representation Selection (patent_led clean v3)

Inputs:
  - seed/seed_publications.txt
  - artifacts/raw_pub_to_family_id.json   (seed_pub -> family_id)

Outputs:
  - artifacts/rep_selection_v3.jsonl

What it does:
  - Calls OPS family endpoint for each seed publication.
  - Extracts publication-like docdb identifiers (processing set).
  - Computes required-set targets: WO A1, EP A/B, US A/B (if present).
  - Emits a clean, governance-auditable JSONL (no raw XML stored).
  - Caching: family XML cached in cache/ops/ (data minimization).

Notes:
  - This step does NOT fetch claims/spec (that is Step C/E).
  - Deterministic, publication-only boundary.
"""

from __future__ import annotations

import os
import re
import json
import time
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import xml.etree.ElementTree as ET

import epo_ops


ROOT = Path(__file__).resolve().parents[1]

SEED_TXT = ROOT / "seed" / "seed_publications.txt"
PUB2FAM_JSON = ROOT / "artifacts" / "raw_pub_to_family_id.json"

OUT_JSONL = ROOT / "artifacts" / "rep_selection_v3.jsonl"
CACHE_DIR = ROOT / "cache" / "ops"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------
# small utils
# ----------------------------
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def sha1_hex(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()

def read_text_lines(p: Path) -> List[str]:
    if not p.exists():
        raise FileNotFoundError(f"Missing file: {p}")
    lines = [x.strip() for x in p.read_text(encoding="utf-8", errors="ignore").splitlines()]
    return [x for x in lines if x and not x.startswith("#")]

def load_pub2fam(p: Path) -> Dict[str, str]:
    if not p.exists():
        raise FileNotFoundError(f"Missing pub2fam map: {p}")
    m = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(m, dict):
        raise ValueError("pub2fam is not a JSON object")
    out: Dict[str, str] = {}
    for k, v in m.items():
        kk = str(k).strip().upper()
        vv = str(v).strip() if v is not None else ""
        if kk and vv:
            out[kk] = vv
    return out

def cache_path(key: str, ext: str = ".xml") -> Path:
    return CACHE_DIR / (sha1_hex(key) + ext)

def read_cache(p: Path) -> Optional[str]:
    return p.read_text(encoding="utf-8", errors="ignore") if p.exists() else None

def write_cache(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")

def localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower() if tag else ""


# ----------------------------
# docdb parsing
# ----------------------------
_KIND_RE = re.compile(r"([A-Z]\d?)$", re.I)

def parse_docdb_concat(pub: str) -> Tuple[str, str, str]:
    """
    Parse 'EP3825599B1' / 'US2021408327A1' / 'WO2024200159A1' -> (cc, number, kind)
    """
    p = (pub or "").strip().upper()
    if len(p) < 4:
        raise ValueError(f"PUB_TOO_SHORT: {pub!r}")
    cc = p[:2]
    m = _KIND_RE.search(p)
    if not m:
        raise ValueError(f"CANNOT_PARSE_KIND: {pub!r}")
    kind = m.group(1).upper()
    number = p[2:-len(kind)]
    if not number or not number.isdigit():
        raise ValueError(f"NON_DIGIT_NUMBER: {pub!r}")
    return cc, number, kind

def to_dotted(cc: str, number: str, kind: str) -> str:
    return f"{cc}.{number}.{kind}"

def is_publication_like(cc: str, number: str, kind: str) -> bool:
    """
    Publication-like filter (governance boundary):
      - numeric doc-number
      - exclude US provisional P
      - exclude EP W (non-publication kind for our endpoints)
      - allow A*/B*/U*
    """
    cc = (cc or "").upper()
    kind = (kind or "").upper()
    number = (number or "").strip()

    if not number.isdigit():
        return False
    if cc == "US" and kind == "P":
        return False
    if cc == "EP" and kind == "W":
        return False
    if kind.startswith(("A", "B", "U")):
        return True
    return False


# ----------------------------
# OPS family fetch (cached)
# ----------------------------
def ops_family_xml(client: epo_ops.Client, seed_pub: str) -> Tuple[str, bool]:
    seed_pub = (seed_pub or "").strip().upper()
    cc, number, kind = parse_docdb_concat(seed_pub)
    model = epo_ops.models.Docdb(number, cc, kind)

    key = f"ops:family:publication:{seed_pub}"
    p = cache_path(key, ".xml")
    cached = read_cache(p)
    if cached:
        return cached, True

    resp = client.family(reference_type="publication", input=model)
    resp.raise_for_status()
    text = resp.text or ""
    write_cache(p, text)
    return text, False


# ----------------------------
# XML extraction
# ----------------------------
@dataclass(frozen=True)
class Pub:
    docdb: str        # concat, e.g. EP3825599B1
    dotted: str       # EP.3825599.B1
    cc: str
    number: str
    kind: str

_KIND_OK = re.compile(r"^[A-Z]\d?$")

def extract_publication_docids(xml_text: str) -> List[Pub]:
    """
    Scan ALL <document-id>, keep only publication-like docdbs with country/doc-number/kind.
    This avoids application/priority leakage.
    """
    out: List[Pub] = []
    try:
        root = ET.fromstring(xml_text)
    except Exception:
        return out

    for el in root.iter():
        if localname(el.tag) != "document-id":
            continue

        cc = None
        num = None
        kind = None

        for ch in list(el):
            nm = localname(ch.tag)
            tx = (ch.text or "").strip()
            if nm == "country":
                cc = tx.upper()
            elif nm in ("doc-number", "docnumber"):
                num = tx.strip()
            elif nm == "kind":
                k = tx.upper()
                kind = k if _KIND_OK.match(k) else None

        if not (cc and num and kind):
            continue
        if not is_publication_like(cc, num, kind):
            continue

        docdb = f"{cc}{num}{kind}"
        out.append(Pub(docdb=docdb, dotted=to_dotted(cc, num, kind), cc=cc, number=num, kind=kind))

    # stable dedupe
    seen = set()
    dedup: List[Pub] = []
    for p in out:
        if p.docdb not in seen:
            dedup.append(p)
            seen.add(p.docdb)
    return dedup


# ----------------------------
# target picking
# ----------------------------
def classify_kind(kind: str) -> Tuple[bool, bool]:
    k0 = (kind or "").upper()[:1]
    return (k0 == "A", k0 == "B")

def pick_one(pubs: List[Pub], cc: str, want: str) -> Optional[str]:
    cc = cc.upper()

    def ok(p: Pub) -> bool:
        if p.cc != cc:
            return False
        is_a, is_b = classify_kind(p.kind)
        if want == "WO_A1":
            return (p.cc == "WO" and p.kind == "A1")
        if want.endswith("_A"):
            return is_a
        if want.endswith("_B"):
            return is_b
        return False

    for p in pubs:
        if ok(p):
            return p.docdb
    return None


# ----------------------------
# main
# ----------------------------
def main() -> int:
    key = os.getenv("OPS_KEY")
    secret = os.getenv("OPS_SECRET")
    if not key or not secret:
        raise SystemExit("Missing OPS_KEY / OPS_SECRET")

    sleep_s = float(os.getenv("OPS_SLEEP_SEED", "0.2"))
    batch_pause_every = int(os.getenv("OPS_BATCH_EVERY", "10"))
    batch_pause_s = float(os.getenv("OPS_BATCH_SLEEP", "0.8"))

    seeds = read_text_lines(SEED_TXT)
    pub2fam = load_pub2fam(PUB2FAM_JSON)

    client = epo_ops.Client(key=key, secret=secret)

    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)

    ok = 0
    err = 0

    with OUT_JSONL.open("w", encoding="utf-8") as f:
        for i, seed in enumerate(seeds, 1):
            seed_u = seed.strip().upper()
            rec: Dict[str, Any] = {
                "artifact_version": "rep_selection_v3",
                "created_at": now_iso(),
                "seed_publication_number": seed_u,
                "family_id": pub2fam.get(seed_u),
                "asset_id": sha1_hex("family|" + (pub2fam.get(seed_u) or seed_u)),
                "evidence": {
                    "seed_source": str(SEED_TXT),
                    "family_id_source_map": str(PUB2FAM_JSON),
                },
                "ops": {"cache_hit_family": None},
                "status": None,
            }

            try:
                xml_text, hit = ops_family_xml(client, seed_u)
                rec["ops"]["cache_hit_family"] = hit

                pubs = extract_publication_docids(xml_text)
                pubs_sorted = sorted(pubs, key=lambda p: (p.cc, p.number, p.kind, p.docdb))

                rec["processing_publications"] = [p.docdb for p in pubs_sorted]
                rec["processing_publications_dotted"] = [p.dotted for p in pubs_sorted]

                # required-set targets (existence will be checked later by gates)
                targets = {
                    "wo_a1_pub": pick_one(pubs_sorted, "WO", "WO_A1"),
                    "ep_a_pub": pick_one(pubs_sorted, "EP", "EP_A"),
                    "ep_b_pub": pick_one(pubs_sorted, "EP", "EP_B"),
                    "us_a_pub": pick_one(pubs_sorted, "US", "US_A"),
                    "us_b_pub": pick_one(pubs_sorted, "US", "US_B"),
                }
                rec["required_set_targets"] = targets

                # claims candidates for Step C (do NOT fetch here)
                # Strategy: anchor on EP/US for training later; still keep WO candidate present for retention.
                claims_candidates: List[str] = []
                # prefer EP A, then US A, then EP B, then US B, then WO A1
                for k in ("ep_a_pub", "us_a_pub", "ep_b_pub", "us_b_pub", "wo_a1_pub"):
                    v = targets.get(k)
                    if v and v not in claims_candidates:
                        claims_candidates.append(v)
                # plus: everything else as tail (for retention completeness in Step C)
                for p in rec["processing_publications"]:
                    if p not in claims_candidates:
                        claims_candidates.append(p)
                rec["claims_candidates"] = claims_candidates

                rec["status"] = "OK"
                ok += 1

            except Exception as e:
                rec["status"] = "ERROR"
                rec["error"] = str(e)
                err += 1

            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

            if sleep_s > 0:
                time.sleep(sleep_s)
            if batch_pause_every and i % batch_pause_every == 0:
                time.sleep(batch_pause_s)

    print(json.dumps({
        "step": "B",
        "out": str(OUT_JSONL),
        "total": len(seeds),
        "ok": ok,
        "error": err
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
