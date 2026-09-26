# PROGRESS.md — Assignment 16 (rendered-geometry-history)

- status: in_progress
- phase: 2 (resumed after coordinator restart-drain; renders: 3,170/24,516; 6 workers on final0-5)
- elapsed_hours: 17.8
- files_written: ~3170
- last_check_in: 2026-09-26T20:10:00Z
- builds_done: 102 / 102
- render_results: 3170
- geometry_size_mb: 20.3
- blockers: none (previous coordinator died from a runtime "restart drain", not a task failure; all state on disk; workers relaunched detached via setsid)

## Status
- Coordinator restarted ~20:06 UTC. Relaunched 6 render workers (final0-5, render16_final.py over shards16/finalN.json, skipping existing geometry files).
- 3,170/24,516 renders done (~13%). Rate ~7-8s/render/worker; ETA ~20-24h for the remainder.
- All existing geometry files verified in the corrected schema: attrs omitted, text_sha 12 hex chars, per-file serving/font_display/font_check/cache_warmed fields.

## Notes
- Phase 3 (deltas), summary recompute, final push pending.
- Push every ~2h via scripts: a16-work/push_a16.py (chunked Git Database API, diffs only 16-rendered-geometry-history/ vs current remote main).
- Remote main at last partial push: 4bd7c343067c372b2a60fc18fbfceff0465c905a.
