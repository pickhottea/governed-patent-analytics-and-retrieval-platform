# scripts/ingest_patents_v3_from_chunks.py
import json
from pathlib import Path
from collections import defaultdict
import hashlib
import requests

ES = "http://localhost:9200"
INDEX = "patents_v3"

P_REP = Path("artifacts/claims_representation_v3.jsonl")
P_CLAIMS = Path("artifacts/chunks_claims_all_v1.jsonl")
P_SPEC = Path("artifacts/chunks_spec_all_v1.jsonl")

FLAG_FAMILY_COLLISION = "FAMILY_COLLISION_PROXY_CLUSTER"


def jloadl(p: Path):
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def pub_to_jur(pub: str) -> str:
    return (pub or "").split(".", 1)[0].upper()


def bulk(actions: list[str]):
    data = "\n".join(actions) + "\n"
    r = requests.post(
        f"{ES}/_bulk",
        data=data,
        headers={"Content-Type": "application/x-ndjson"},
        timeout=180,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"bulk failed {r.status_code}: {r.text[:500]}")
    out = r.json()
    if out.get("errors"):
        items = out.get("items", [])[:8]
        raise RuntimeError(f"bulk errors: {json.dumps(items, ensure_ascii=False)[:1200]}")
    return out


def main():
    # 1) representation：可能同 pub 多筆（不同 dataset family）
    rep_by_pub = defaultdict(list)
    for o in jloadl(P_REP):
        pub = o.get("selected_publication")
        if not pub:
            continue
        rep_by_pub[pub].append(
            {
                "family_id": o.get("family_id"),
                "asset_id": o.get("asset_id"),
                "claims_source": o.get("claims_source"),
                "governance_flags": o.get("governance_flags") or [],
                "selected_source": o.get("selected_source"),
                "seed_publication_number": o.get("seed_publication_number"),
            }
        )

    # 2) 收集 claims/spec（按 pub 聚合）
    claims_by_pub = defaultdict(list)
    for o in jloadl(P_CLAIMS):
        pub = o.get("selected_publication")
        txt = (o.get("text") or "").strip()
        if pub and txt:
            claims_by_pub[pub].append(txt)

    spec_by_pub = defaultdict(list)
    for o in jloadl(P_SPEC):
        pub = o.get("selected_publication")
        txt = (o.get("text") or "").strip()
        if pub and txt:
            spec_by_pub[pub].append(txt)

    pubs = sorted(set(rep_by_pub.keys()) | set(claims_by_pub.keys()) | set(spec_by_pub.keys()))
    # 這裡的 rep_count 用「pub 的數量」跟「rep row 數量」分開看比較不會誤會
    rep_rows = sum(len(v) for v in rep_by_pub.values())
    print(
        f"[info] pubs={len(pubs)} rep_pubs={len(rep_by_pub)} rep_rows={rep_rows} "
        f"claims_pubs={len(claims_by_pub)} spec_pubs={len(spec_by_pub)}"
    )

    # 3) 偵測 pub collision（同 pub 對應多個 dataset family）
    collision_pubs = {
        pub for pub, lst in rep_by_pub.items()
        if len({x.get("family_id") for x in lst if x.get("family_id")}) > 1
    }
    if collision_pubs:
        print(f"[warn] detected pub collisions: {len(collision_pubs)} (will add flag {FLAG_FAMILY_COLLISION})")
        # 你如果想看是哪幾篇，打開下面這行
        # print("collision pubs sample:", sorted(list(collision_pubs))[:10])

    actions = []
    sent_docs = 0

    for pub in pubs:
        jur = pub_to_jur(pub)

        claims = "\n".join(claims_by_pub.get(pub, []))
        spec = "\n".join(spec_by_pub.get(pub, []))

        # 如果 rep 沒有這個 pub，就還是可以 ingest（但 family/meta 會是 None）
        metas = rep_by_pub.get(pub) or [None]

        for meta in metas:
            meta = meta or {}

            family_id = meta.get("family_id")
            asset_id = meta.get("asset_id")

            # doc_id：用 pub|family_id，確保 1 pub 可以有多筆（嚴格分析需要）
            # 若 family_id 缺失，就退回 pub-only（仍然穩定）
            if family_id:
                doc_id = sha1("pubfam|" + pub + "|" + str(family_id))
            else:
                doc_id = sha1("pub|" + pub)

            flags = list(meta.get("governance_flags") or [])
            if pub in collision_pubs and FLAG_FAMILY_COLLISION not in flags:
                flags.append(FLAG_FAMILY_COLLISION)

            doc = {
                # ---- identity ----
                "doc_id": doc_id,  # 方便 debug/UI，不必依賴 ES _id
                "pub_canonical_id": sha1("pub|" + pub),  # 方便「按 pub 聚合」的 UI/analysis
                "selected_publication": pub,
                "jurisdiction": jur,

                # ---- dataset identity ----
                "family_id": family_id,
                "asset_id": asset_id,

                # ---- governance ----
                "claims_source": meta.get("claims_source"),
                "selected_source": meta.get("selected_source"),
                "seed_publication_number": meta.get("seed_publication_number"),
                "governance_flags": flags,

                # ---- content ----
                "has_claim1": False,
            }

            if claims:
                doc["claims_all"] = claims
                # 先用很粗的判斷當 MVP；之後你也可以改成用 chunks_claims 裡的 claim_no==1
                doc["has_claim1"] = ("1." in claims[:4000]) or ("1 " in claims[:2000])

            if spec:
                doc["spec"] = spec

            actions.append(json.dumps({"index": {"_index": INDEX, "_id": doc_id}}, ensure_ascii=False))
            actions.append(json.dumps(doc, ensure_ascii=False))
            sent_docs += 1

            if sent_docs % 200 == 0:
                bulk(actions)
                actions = []

    if actions:
        bulk(actions)

    print(f"[ok] indexed docs={sent_docs} into {INDEX}")


if __name__ == "__main__":
    main()
