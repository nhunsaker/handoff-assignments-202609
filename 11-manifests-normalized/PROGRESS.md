# Assignment 11 — PROGRESS

- status: complete (accepted; review round 1)
- phase: REVIEW.md correction — add PROGRESS.md per README protocol (2026-09-26)
- elapsed_hours: 0.1
- files_written: 1 (this PROGRESS.md)
- last_check_in: 2026-09-26T17:20:00Z
- blockers: none

## Work done

- Built and normalized manifests for 102/102 tempertemper commits (window from
  assignment 10); `manifests_failed: 0`, `failed_shas: []`.
- `output/manifests/` holds 102 per-commit manifest files; `output/pairs.json`
  covers 101 consecutive pairs (101/101 both built).
- Median pages modified per pair: raw 526, normalized 523, body 5.
- Determinism control agrees with assignment 13 (06f96f78 raw-identical;
  2cda2bdd raw-differs on all 592 pages, normalized and body on none).
- 48 snapshot pairs recorded (`output/snapshots/`, 1971 files, ~100 MB):
  the insertion pair 74056980e→5e38769bf changes 355 page bodies — one new
  post touches two-thirds of the site.

## Review return (round 1, accepted)

- Rebuilt 74056980e and 5e38769bf independently in node:22.13.1 — 519 and
  520 pages, matching the manifests.
- Recomputed raw, normalized and body sha256 for five pages at each commit
  (blog/index, 404, about, blog/year/2025, category/accessibility): 30 of 30
  hashes identical to manifests/<sha>.json.
- Note: the normalized hash barely reduces cross-commit churn (median raw 526,
  normalized 523, body 5). Cause is the brief's rule, not the work: at release
  commits the cache-buster is the site version (`?v=6.5.23`), and
  `(\\?v=)\\d+` rewrites only the leading digits. The body hash is the change
  signal. No action needed.
- REVIEW.md requested this PROGRESS.md ("with the return manifest, as for 10,
  12 and 13") — this file is that addition.
