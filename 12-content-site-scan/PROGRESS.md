# Assignment 12 — PROGRESS

- status: corrections_complete
- phase: review corrections C1–C5 (all applied; not pushed — parent handles delivery)
- elapsed_hours: 0.1
- files_written: 10
- last_check_in: 2026-09-26T12:46:31Z
- blockers: none

## Log

- 2026-09-26T12:41Z: started. Read ASSIGNMENT.md and the REVIEW.md correction
  list (C1–C5). No PROGRESS.md check-in protocol exists in this assignment's
  README; followed the 14-element-key-stability/PROGRESS.md format.
- 2026-09-26T12:42Z: C2 — verified `antrea-io/website` has `bucket: "H"` in
  candidates.json (present in both output/candidates.json and
  output/candidates_h.json, status kept) and sits at rank #3 of 14 in
  summary.json `qualifying_corpus_ranked` with `bucket: null`. Moved both
  candidate rows to `status: rejected` with reason "project website of a
  Kubernetes networking tool — documentation for a developer tool".
  Root cause of the null bucket: output/tmp_finish12/build_summary.py joined
  bucket via `probe['bucket']`, but probe files carry no bucket field; the
  join is now candidates.json keyed by repo. The same join had also dropped
  jacobtomlinson/website (H, broken) and reillypascal/personalsite-ssg (E,
  environment_incomplete) from per-bucket probe counts; the fix restores them.
  Re-ranked corpus: 13 rows, antrea absent, order otherwise unchanged
  (Brett-Tanner/souls-like-strings is now #3).
- 2026-09-26T12:43Z: C3 — verified neither windows_h.json nor windows_ej.json
  carried a qualifies/qualified field (0/42 and 0/34). EJ's effective recompute
  rule counted every row in the file per its bucket (E 26/26, J 8/8, regardless
  of verdict), so `qualifies: true` was added to all 42 windows_h.json rows,
  all 34 windows_ej.json rows, and all 76 windows.json rows (the merged file,
  which takes precedence in the merge). Recomputed per-bucket
  qualifying_windows: H 41, E 26, J 8 (funnel 75). H is 41 not 42 because the
  recompute counts only intake-kept repos and antrea-io/website's window is
  excluded per C2.
- 2026-09-26T12:44Z: C4 — surveyed all 27 probes: exactly 376 Phase 7 rows with
  `cause: "unclassified"` and empty quote, all in
  output/probes/erikkroes__erikkroes-nl.json, all raw-only
  (raw_differs=true, body_differs=false). Classified all 376 as: "cache-bust
  timestamp in <head> (og:image/twitter:image 11ty screenshot-service URL
  embeds build-time epoch milliseconds via new Date().valueOf(); <body>
  subtree identical)", with one quote region per cause (the rendered og:image
  meta region; only the trailing _<13-digit epoch-ms> varies per build).
  Mechanism verified verbatim in the on-disk clone
  (work/probe12e/erikkroes__erikkroes-nl/clone/.eleventy.js lines 85-93:
  `const cacheKey = `_${new Date().valueOf()}`;` feeding head.njk's og:image /
  twitter:image tags). No build outputs were retained on disk and rebuilding is
  out of scope, so the quote documents the verbatim generator. 0 unclassified
  rows remain; distinct_causes populated; verdict stays corpus_ready,
  all_body_identical stays true.
- 2026-09-26T12:45Z: C1 — added top-level `funnel_coverage` to summary.json:
  buckets A (Astro) and N (Next/Nuxt/SvelteKit/Gatsby) stopped after intake
  (60 kept each; recorded in candidates.json / candidates_n.json); screening,
  windowing and probing covered H, E, J only within this run's budget; A/N
  intake candidates are ready for a future pass. output/.progress_summary.json
  no longer claims 100% of the full funnel: added `scope` field recording 100%
  of the H/E/J probe phase only.
  Before: `{"current_stage":4,"progress_percent":100,"stage_name":"summary.json
  write",...,"status":"complete","total_stages":4}` (no scope).
  After: same + `"scope":"H/E/J probe phase only: 100% of
  screening/windowing/probing for buckets H, E, J. Buckets A (Astro) and N
  (Next/Nuxt/SvelteKit/Gatsby) stopped after intake (60 candidates kept each);
  they were never screened, windowed or probed in this run."`
- 2026-09-26T12:46Z: recompute re-run; all summary.json arithmetic validated
  (per-bucket sums equal funnel totals; ranking sorted desc; 13 ranked rows,
  no null buckets). All touched JSON parses.

## Return manifest (output/ files touched or verified)

Touched:
- output/summary.json — recomputed: funnel_coverage added; antrea re-ranked
  out (13-row corpus); per-bucket counts corrected (see before/after below);
  intake_note updated (306 kept, H69).
- output/candidates.json — antrea-io/website -> rejected + reason (C2).
- output/candidates_h.json — antrea-io/website -> rejected + reason (C2).
- output/windows_h.json — qualifies:true on all 42 rows (C3).
- output/windows_ej.json — qualifies:true on all 34 rows (C3, schema parity).
- output/windows.json — qualifies:true on all 76 rows (C3, merged file).
- output/probes/erikkroes__erikkroes-nl.json — 376 Phase 7 rows classified (C4).
- output/.progress_summary.json — scope field added (C1).
- output/tmp_finish12/build_summary.py — bucket join via candidates.json;
  kept-repo filter for windows/probes; qualifying_windows counts qualifies rows;
  funnel_coverage + intake_note; recompute text documents the joins.

Verified (read-only): output/screen.json, output/screen_ej.json,
output/screen_h.json, output/candidates_e.json, output/candidates_j.json,
output/candidates_n.json, all 27 output/probes/*.json (verdict/bucket survey),
work/probe12e/erikkroes__erikkroes-nl/clone/.eleventy.js and
src/templates/parts/head.njk (C4 evidence), output/tmp_finish12/run_erikkroes.log.

Not touched: probe files for other repos; tmp_* scratch files; screen/candidate
shards other than those listed.

## Before/after (corrections)

- funnel: intake_kept 307 -> 306; intake_rejected 1174 -> 1175 (+1 reason:
  "project website of a Kubernetes networking tool — documentation for a
  developer tool"); screened 187 -> 186; static_output_pass 94 -> 93;
  index_pages_pass 86 -> 85; no_build_time_fetch_pass 76 -> 75;
  qualifying_windows 76 -> 75; probed 27 -> 26;
  verdicts corpus_ready 14 -> 13 (nondeterministic 5, environment_incomplete 4,
  broken 3, no_list_insertions 1 unchanged).
- per_bucket H: intake_kept 70 -> 69; screened 70 -> 69; static 51 -> 50;
  index 49 -> 48; nofetch 42 -> 41; qualifying_windows 0 -> 41; probed 14 -> 15;
  verdicts broken 1 -> 2 (jacobtomlinson restored by join fix), corpus_ready 7
  unchanged, others unchanged.
- per_bucket E: probed 9 -> 10; verdicts +environment_incomplete 1
  (reillypascal restored by join fix); qualifying_windows 26 unchanged.
- per_bucket J: unchanged. per_bucket A/N: unchanged (intake only, 60 kept each).
- qualifying_corpus_ranked: 14 -> 13 rows; antrea-io/website (old #3, bucket
  null) removed; every rank below old #3 shifted up one; no null buckets remain.

## Recompute statement

`python3 output/tmp_finish12/build_summary.py` (run from
12-content-site-scan/) recomputes output/summary.json from:
output/candidates.json (+ candidates_e/h/j/n.json shards),
output/screen.json (+ screen_ej.json, screen_h.json),
output/windows.json (+ windows_ej.json, windows_h.json),
output/probes/*.json (excluding *.p7builds.json helpers).
Bucket for windows/probes is joined from candidates.json by repo; screens,
windows and probes are counted only for intake-kept repos; qualifying_windows
counts rows with qualifies=true. Corpus rank score =
median_static_pages * new_content_commits_in_window, sorted descending.
