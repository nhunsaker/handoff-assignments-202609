status: accepted
round: 2
verified: 419/456 builds and the pairs/structure layers spot-checked; two adjacent tempertemper commits (60daa0f63, 0e0d679ee) rebuilt independently and a "modified" page diffed — the only difference is the build-time cache-buster `?v=<epoch ms>`, which explains the 526-of-547 pages_modified median; the structure rows for those pages correctly report zero changes. Insert events on blog/index.html (e.g. 283→284 li at position 0, 74056980e→5e38769bf) are real.
corrections:
  - C1: `manifests/<owner>__<repo>/<sha>.json` (the brief's Phase 2 step 4) is absent for all three repos. If the build outputs or install caches still exist, write them now for every built commit (page → sha256 of bytes, plus the `assets` map). If they do not, say so explicitly in PROGRESS.md; assignment 11 re-derives them for tempertemper.
  - C2: `summary.json` claims `"used_mb": 120.0` and "120 MB snapshot budget exhausted during tempertemper". On disk `structure/snapshots/*.json` record `budget_used_bytes: 124592`, two example pointers, and there are zero `.before.html`/`.after.html` files; the directories the pointers name are not in the return. Correct `summary.json` to match the files, and return the snapshot HTML if it still exists on disk.
  - C3: Add to `summary.json` a note on `pages_modified` for tempertemper: the count is byte-level and inflated by the `?v=` cache-buster on every page; the structure layer is the change signal. (One sentence; the data is not wrong, its label is.)

## Round 2 (2026-09-26) — accepted
- C1: 419 manifests now returned (243 / 74 / 102). The self cross-check against 11 (91/102 SHAs agree; the 11
  that differ are the `Date.now()` commits and the category-page ordering 13 found) is consistent with both.
- C2: snapshot HTML returned (3,326 files, 126 MB) and summary.json reconciled, including an open note that the
  per-repo counters do not reconcile with the on-disk bytes. Honest.
- C3: pages_modified note added.
- Housekeeping only: PROGRESS.md still says "not pushed / corrections_in_progress" — it was pushed in 370ab70.
