# Assignment 15 — PROGRESS

- status: in_progress
- phase: 2/2 complete (analysis done; pushing)
- elapsed_hours: 2.0
- files_written: output/{environment,pages,summary,manifest}.json, boxes/ (550), results/ (50)
- last_check_in: 2026-09-26T16:20:00Z
- blockers: PARALLEL-WORKER COLLISION (see log 16:05Z) — second agent active in same folders until ~15:45Z, now quiet 35+ min; parent arbitration needed

## Log
- 2026-09-26T15:30:00Z: started. Read ASSIGNMENT.md in full. Remote main at
  f2773724eda20bf4f19c36af442abcdbc1733b3c (verified via git ls-remote).
- README has no "Shared rendering settings" or "geometry schema" sections
  (grep found nothing); recording viewport 1280x800 / Chromium 152.0.7977.82
  (Playwright, /opt/meta-chromium/chrome) and a self-defined geometry schema
  in environment.json.
- Plan: 40 pages from tempertemper / alexcarpenter / efcl built at latest
  buildable window commits (tempertemper 2cda2bdda6b7cca5c7d5c169eda1f7e867e0f236,
  efcl ef5717299a895401388a1c880bf6b313a7ed227e, alexcarpenter
  4c5da684256c327fef8c0207d2dee3175f6c3dfd — the last alexcarpenter window commit
  d1329b68758a2be1237c9b3527cd30b928843849 failed install, so latest buildable
  is used), plus 10 pages from other 08-probe-list sites with third-party embeds.
- Local git mirrors present at 10-build-history-diffs/work/mirrors/.
  Assignment 14's work cache/builds are empty; doing own builds in
  ~/workspace/a15-work (excluded from push).
- Builds of the three sites starting now (background); cloning 08-probe-list
  candidate repos from GitHub and grepping source for iframe/third-party embeds
  in parallel.
- 2026-09-26T15:35Z: all three sites built OK (tempertemper 592 html eleventy,
  efcl 945 html jekyll, alexcarpenter 80 html astro; build_site.sh fixed: fnm
  env needs --shell bash under backgrounded exec). Render harness tested:
  file:// URLs (localhost blocked by Chromium Local Network Access checks in
  sandbox); C1 aborted 6 font requests on tempertemper blog index, C5 aborted
  7; C2/C4 blocked 0 there (no images / no third-party requests on that page).
  output/environment.json written (geometry schema, conditions, site commits).
  Two subagents running: 40-page selection for the three sites; 08-probe-list
  third-party embed source search (17 repos).
- 2026-09-26T15:45Z: page-selection subagent done but raced the alexcarpenter
  rebuild (read the pre-fix log, reported build failed; the fixed rebuild had
  completed: dist/ with 80 html). Corrected the scheme to the spec's three
  sites: tempertemper 14 + efcl 13 + alexcarpenter 13 = 40. output/pages.json
  written (40 pages, kinds, titles, embed findings; efcl/alexcarpenter lack
  year archives — documented). Waiting on the 08-probe embed search for the
  10 third-party pages.
- 2026-09-26T16:05Z (second worker): PARALLEL-WORKER COLLISION. A second agent
  is concurrently executing this same assignment in the same folders
  (~/workspace/a15-work and 15-external-resource-layout/output). Evidence:
  output/environment.json + output/pages.json written 15:27:10/15:27:38Z,
  a15-work/render_one.py + render_shard.py written 15:25-15:27Z, and
  a15-work/render_worker.py was overwritten at 15:32:02Z with a hybrid
  version (correct URL rewrite but wildcard routing, site_dir=file dirname
  bug, no sidecar) AFTER the validated worker was smoke-tested. Four render
  workers launched ~15:32Z loaded the overwritten version and produced ~213
  invalid boxes files (fonts_check False on pages that load webfonts).
  All four workers killed, all boxes deleted. render_worker.py rewritten
  (final design: per-request blocking rules, no C0 dependencies/sidecars,
  site_dir explicit per task, page-sharded tasks), tasks regenerated
  (tasks/w0-w3.jsonl, 40 pages x 11 = 440 tasks, page IDs tt-*/efcl-*/ac-*).
  Adopted 3 page-selection improvements from the parallel pass:
  tempertemper year archive -> blog/year/2023.html, efcl +tags/index.html,
  alexcarpenter gear/coffee/index.html (replacing gear/index.html).
  Smoke tests pass (nested pages load CSS/fonts; C1 aborts fonts).
  5 workers running: w0-w3 (40 main pages), w4 (10 third-party pages).
- 2026-09-26T16:05Z: 10 third-party-embed pages selected from Assignment 08
  probe-list sites using Assignment-13 proven builds: querkmachine/beeps.website
  @74dc73cd551a (3 pages with youtube-nocookie iframes) and cubxxw/blog
  @fed853722c17 (7 pages with utteranc.es <script src=https://utteranc.es/client.js>).
  Exact embed markup recorded in a15-work/embeds.json. 11tybundle.dev rejected:
  build requires author's local /Users/Bob/Dropbox/... data files (genuine).
- 2026-09-26T16:20Z: Phase 1 complete: 550/550 renders (440 main + 110 extra),
  0 errors. Phase 2 complete: results/ for 50/50 pages; summary.json recomputed
  via recompute_summary.py and every number independently verified.
  Key finding: 10/50 pages show run-to-run jitter, all tempertemper, all caused
  by font-display:optional webfont race on "FS Me Web" (quoted @font-face rule
  in results). 8 condition-entries flagged race_confounded (C2/C4 with 0 blocked
  requests but differing elements). C4 truly affected 0 pages by third-party
  blocking (the 3 nominal are race artifacts); efcl-home's googletagmanager
  block caused no layout change. manifest.json written (604 files, 9.3MB).
