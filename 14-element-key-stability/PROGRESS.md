# Assignment 14 — PROGRESS

- status: in_progress
- phase: 1 (rebuilds + measurements running in parallel)
- elapsed_hours: 1.5
- files_written: 8
- last_check_in: 2026-09-26T13:00:00Z
- blockers: none

## Log
- 2026-09-26T12:20:00Z: started. Read ASSIGNMENT.md. Remote main verified at
  1aa9eb2a7fc0286a4eff256e0bf721afde4fabc1 via GitHub API. GitHub credential
  (custom.github) works. Local mirrors for all three repos present; fnm node
  versions and rbenv ruby 3.2.2 present.
- 2026-09-26T12:21:00Z: event selection complete — 300 events
  (150 tempertemper / 100 alexcarpenter / 50 efcl), all on distinct
  (pair, page) combos, pairs chosen as runs of consecutive pairs spread over
  each window (round-robin within runs). 184 unique commits to rebuild.
  -> output/events.json
- 2026-09-26T12:22:00Z: rebuild driver bugs found and fixed: (1) page
  subdirectory missing on save (FileNotFoundError); (2) Assignment 10 cache
  path used short site name instead of full repo id, so no cache hits;
  (3) kill-truncated cache entries poisoned later hits — now atomic
  (copytree to tmp + os.replace) and empty dirs treated as misses;
  (4) cross-shard cache-save race — now race-safe. State wiped, clean restart
  with 2 shards.
- 2026-09-26T12:27:00Z: rebuilds running (2 shards, 184 commits). keys.py
  (Phases 1-3), keys.json, recompute_summary.py, environment.json, push14.py
  written. First push (meta) at 757761c5 (verified via ls-remote).
- 2026-09-26T13:00:00Z: rebuilds 16/184 commits, all build_ok. keys.py bugs
  fixed: (1) K8 sibling lookup included <head> (not under body) — now
  restricted to elements under body; (2) K1 value was css_path not outerHTML
  — now Kb[K1]=normalized outerHTML; (3) relation buckets renamed to spec
  names (in/above/below/outside_group); 'in' implemented literally (provably
  empty for K1-matched pairs). Added event recomputation QA (10's exact
  group_events logic) -> event_reproduced_in_rebuild flag. Measurement
  workers (4 shards, polling) started. 2/300 results written.
  FINDING: alexcarpenter gear pages have nondeterministic item order across
  builds (same commit, same toolchain, different order). 9/300 events are on
  gear pages. Events kept with QA flags; stability/false-match remain valid
  (ground truth from rebuilt pages).
