status: accepted
round: 1
verified: rebuilt 74056980e and 5e38769bf independently in node:22.13.1 — 519 and 520 pages, matching the manifests; recomputed raw, normalized and body sha256 for five pages at each commit (blog/index, 404, about, blog/year/2025, category/accessibility): 30 of 30 hashes identical to manifests/<sha>.json. Determinism control agrees with assignment 13 (06f96f78 raw-identical; 2cda2bdd raw-differs on all 592 pages, normalized and body on none).
notes:
  - The normalized hash barely reduces cross-commit churn (median pages modified per pair: raw 526, normalized 523, body 5). Cause is the brief's rule, not the work: at release commits the cache-buster is the site version (`?v=6.5.23`), and `(\?v=)\d+` rewrites only the leading digits. The body hash is the change signal. No action needed.
  - The insertion pair 74056980e→5e38769bf changes 355 page bodies: one new post touches two-thirds of the site.
  - No PROGRESS.md (README protocol) — please add one with the return manifest, as for 10, 12 and 13.
