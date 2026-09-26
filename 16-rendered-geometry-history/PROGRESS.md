# PROGRESS.md — Assignment 16 (rendered-geometry-history)

- status: in_progress
- phase: 1 (builds: 57/102 done; size projection complete, calibration underway)
- elapsed_hours: 1.5
- files_written: 6
- last_check_in: 2026-09-26T17:55:00Z
- builds_done: 57 / 102
- render_results: 0
- geometry_size_mb: 0.0
- blockers: none

## Notes
- Size projection (manifests + lxml element counts over all 102 commits): 40,200 jobs, 8,089,530 elements. Projected geometry/: full schema 472.8 MB; drop attrs 415.7 MB; drop 390x844 for non-list pages 314.6 MB; both drops 276.4 MB. None of the spec's drop scenarios fit the 180 MB budget (the assignment's "~2,000 page renders" estimate vs 40,200 actual — many commits changed site-wide templates).
- Running a 30-page calibration render to measure true gz bytes/element before finalizing the drop decision. If the spec's drops remain insufficient, the minimal further reduction (documented exactly in summary.json) will be applied.
- Push plan: chunked Git Database API per the assignment-14 template (adapted to ~/workspace/a16-work/push_a16.py), incremental pushes as phases complete; stop on 403 rate limit per instructions.
- Test render verified: schema matches ASSIGNMENT.md; web font loads ("FS Me Web"); attrs record as-served file:// URLs (documented in environment.json).
