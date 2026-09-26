status: corrections_requested
round: 2
verified: erikkroes/erikkroes-nl (ranked #2) rebuilt independently in node:24 — 1a69abc828 → 251 pages, 51d8eaae34 → 753 pages, exactly as the probe reports; two builds of 51d8eaae34 have identical <body> on all 753 pages (376 differ in raw bytes only, via a build-time epoch-ms suffix in the og:image URL in <head>). The funnel's non-ready verdicts read correctly (e.g. wecount.inclusivedesign 335 body-differing pages → nondeterministic; spotlightpa static list length → no_list_insertions). 13 corpus_ready repositories is the best yield of any scan.
corrections:
  - C1: Buckets A (Astro, 60 kept) and N (Next/Nuxt/SvelteKit/Gatsby, 60 kept) were never screened (summary per_bucket: screened 0), yet .progress_summary.json says `complete, 100%`. Either screen, window and probe them, or state plainly in summary.json and PROGRESS.md that the funnel stopped after intake for A and N and why. The brief's rule stands: "if you run out of time, return what finished and say how far the funnel got."
  - C2: `antrea-io/website` (ranked #3) is the project website of a Kubernetes networking tool — documentation for a developer tool, which intake rejects. Move it to the intake rejections with that reason and re-rank. It also appears with `bucket: null` in qualifying_corpus_ranked although candidates.json has `bucket: "H"` — fix the join that dropped it.
  - C3: per_bucket H says `qualifying_windows: 0` but `probed: 14`. windows_h.json rows carry no `qualifies`/`qualified` field, so the recompute counted zero. Add the field to windows_h.json (and check windows_ej.json uses the same schema) and recompute.
  - C4: Phase 7 rows record `cause: "unclassified"` with an empty quote for raw-only differences. Classify them (e.g. erikkroes: build-time epoch ms in the og:image URL) and quote one region per cause, as the brief asks.
  - C5: No PROGRESS.md (README protocol). Add one with the return manifest and the recompute statement.

## Round 2 (2026-09-26) — one correction left
Accepted: C1 (funnel_coverage states A/N stopped after intake — acceptable under the brief), C2 (antrea rejected; the
join bug fixed, which also restored jacobtomlinson and reillypascal to the counts), C4 (the erikkroes cause, traced
to `.eleventy.js` lines 85–93, matches an independent rebuild exactly), C5 (PROGRESS.md).
corrections:
  - C3-R2: The C3 fix set `qualifies: true` on EVERY window row. 49 rows now contradict their own verdict:
    windows_h.json 26 (24 `no_window`, 2 `too_few_new_content`; e.g. verifa/website, whose notes say "best window
    has 2 < 25 page-touching commits"), windows_ej.json 23 (20 `no_window`, 2 `too_few_new_content`,
    1 `clone_failed`). Set `qualifies` from the verdict (`verdict == "window_ok"`), in windows_h.json,
    windows_ej.json and the merged windows.json, and recompute summary per_bucket qualifying_windows — expected
    H 16, E+J 11 (not 41 / 26 / 8). The ranked corpus is unaffected (probes ran only on window_ok rows).
