# deprecated_archive

This folder contains retired pipeline scripts kept for traceability only.

Rules:
- DO NOT execute these scripts in any active workflow.
- They may rely on outdated assumptions (e.g., mixed OPS/Google lanes, old chunking rules, incomplete metadata).
- If a script is ever revived, it must be ported into `scripts/canonical/` with a new version and documentation.

Purpose:
- Historical audit / post-mortem
- Reproduce old baselines if needed (explicitly, not by accident)
