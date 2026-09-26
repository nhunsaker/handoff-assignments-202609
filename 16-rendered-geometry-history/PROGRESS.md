# PROGRESS.md — Assignment 16 (rendered-geometry-history)

- status: in_progress
- phase: 1 (builds: 50/102 done; page sets and render shards after builds finish)
- elapsed_hours: 0.6
- files_written: 4
- last_check_in: 2026-09-26T17:00:00Z
- builds_done: 50 / 102
- render_results: 0
- geometry_size_mb: 0.0
- blockers: none

## Notes
- Render approach adapted from assignment 15 (file:// + Playwright route-fulfill with root-relative URL rewrite); worker at ~/workspace/a16-work/render16.py matches the assignment schema.
- Test render on commit 1 index.html at both viewports: OK. 144 elements, ~10KB gz per page, ~5s per render, web font loaded ("FS Me Web", sans-serif; document.fonts.check true).
- attrs records URLs as served (root-relative rewritten to absolute file:// URLs rooted at the built site dir); documented in output/environment.json.
- Build loop (~/workspace/a16-work/build_all.py -> ~/workspace/a16-work/builds/<sha12>/): all commits building OK (eleventy, dist); npm ci only when package.json/package-lock.json change between commits.
- Page-set calibration from manifest body hashes: 20,100 pages at one viewport = 40,200 renders across both viewports (per-commit pages min 41, median 47, max 590; 41 commits with >100 pages due to site-wide template changes).
- Size calibration: ~57.8 gz bytes/element with attrs, ~50.4 without (attrs compress well; dropping them saves only ~13%). Full size projection from per-page lxml element counts will run after builds finish, before scaling renders. Drop order per spec: attrs first, then 390x844 for non-list pages; recorded in summary.json.
