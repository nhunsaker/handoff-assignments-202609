# 13-build-determinism — REVIEW.md corrections progress

- status: corrections_complete (local application only; NOT pushed — delivery is the parent agent's)
- phase: C1–C5 applied and validated
- elapsed_hours: ~2.5
- files_written: 1 (this file) plus edits to 16 existing output files (see return manifest)
- last_check_in: 2026-09-26T12:51:23Z
- blockers: none
- push_status: NOT pushed. Nothing in 13-build-determinism/output is tracked by git
  (all output files show as untracked in `git status --short`); delivery/commit is out of scope.

## Return manifest (every file touched or verified)

Written/edited by this correction pass:
- output/rules.json — C2 scoped withdrawal of shiki-unwrap off nemanjam; C3 added
  derived_from (site, commit, file, difference_id, verbatim region_before/region_after)
  to every surviving rule; 8 rules removed. 30 → 22 active rules.
- output/rules-history.json — added `withdrawals` array (9 entries: 8 full + 1 scoped),
  each with correction tag (C2/C3), UTC timestamp, reason, and full rule snapshot;
  final_rule_count 22; final_rule_ids recomputed.
- output/summary.json — C4: added `b1_b3_evaluation` and `b1_b4_evaluation` per site
  (per commit {identical_before, identical_after, total} mapped from evaluation total_common,
  or {"status":"missing_keep"} verbatim where the evaluation has no build);
  rule lists/counts updated for nemanjam (0), tempertemper (2), beeps (2), yunyuyuan (9);
  nemanjam row: reproducible=false with explicit reason (generated content + 52 one-build-only paths).
- output/differences/nemanjam__nemanjam.github.io.json — C2: the two generated-content
  differences (6333be10bf83 excerpt truncation; 7fed9b43b849 random-OG-background) reclassified
  cause random_id → live_data with other: "generated content" and a verbatim note.
- output/evaluation/signal_<site>.json (12 files) — C1: added region_analysis per rule
  (matcher documented below); the 6 nemanjam entries flagged withdrawn:true with reason,
  region numbers retained as measurement evidence.

Verified read-only (no writes):
- output/differences/*.json (all sites) — C3 grounding source; C2 evidence greps.
- ~/workspace/13-scratch/<site> retained build dirs — C1 signal pairs and C3 impact checks.

## Recompute statement

Nothing in this pass was recomputed from the builds: evaluation identical_before/after
counts were carried forward verbatim. C4 values were asserted exactly equal to
evaluation/<site>.json per commit (validation script, see below). Withdrawing
category-page-num-mask, beeps-redaction-mask, and nuxt-tz-bare does not change any
evaluation after-count: each was applied alone to the retained b1↔b2 builds
(tempertemper 2cda2bdd; beeps 23276fd8, 477a1f74; yunyuyuan 40b7bb51, a28de421, f50767bf)
and flipped 0 page equalities.

## C1 matcher (region-level signal-loss analysis)

For each rule, over the common pages of the site's signal pair (b1 of commit A vs b1 of
commit B), the script /tmp/c1_region_analysis.py (ephemeral, not in repo):
- regex rules: compiled the rule's own pattern, matched raw text, paired matches by
  document order within common files, normalized each match with match.expand(replacement);
- DOM rules (shiki-unwrap, chroma-text): parsed with lxml.html using explicit XPath
  translations (pre.astro-code span | pre[data-theme] span; div.highlight);
- reported regions_matched, regions_differing_raw, regions_differing_across_commits
  (raw differences erased by normalization), regions_preserved_but_differing, unpaired
  counts, up to 5 verbatim examples, and recomputed signal_lost.
- Five XML-only rules had no retained XML/OPML in their signal-pair build dirs and were
  explicitly marked "not_measurable" rather than scored.

## Missing outputs / not-measurable notes

- elsbrock/hetzner-radar: SPA signal pair emitted zero HTML; zero rules; nothing to measure.
- hnpf/stabbed.wtf: one common page; efcl/efcl.github.io: 935 common pages — neither site
  has rules; nothing to measure.
- Five XML-only signal rules (feed-updated, sitemap-lastmod ×2, opml-datecreated,
  godruoyi-pubdate) lacked retained XML/OPML in their signal-pair build dirs, so their
  signal-pair region measurements are recorded as not_measurable; their derived_from
  citations come from the recorded difference regions (D1/D2/D3), not from the signal pair.
- nemanjam-more-posts: no "More posts" region exists in the differences file (grep count 0)
  and the rule pattern does not match the actual build HTML — withdrawn under C2+C3.

## C2 evidence (commands run 2026-09-26, UTC)

- `grep -c "Dolor velit excepteur cupidatat" output/differences/nemanjam__nemanjam.github.io.json`
  → 3 (region_before, region_after, and the C2 reclassification note; quote:
  "Dolor velit excepteur cupidatat aute in fugiat id reprehenderit ipsum qui tempor fugiat.
  Excepteur tempor culpa velit duis quis…")
- `python3 -c "d['commits']['6333be10bf83']['b1_b2']"` →
  {"same_path_differ": 17, "only_in_b1": 52, "only_in_b2": 52}

## C3 citations (one grounded difference per active rule)

- shiki-unwrap: alexcarpenter D2 (notes/index.html, e3641869d63e); rimzzlabs D4 (328e90f173aa)
- cache-buster-q: tempertemper D-cache-buster (2cda2bdda6b7); beeps D1
- category-order-mask: tempertemper D-category-order (2cda2bdda6b7)
- chroma-text: cubxxw D1 (e302344a57a8; region is a fragment — div.highlight wrapper outside the ±context window; documented in citation note)
- nuxt-prerenderedAt D10, nuxt-time-gmt D1, nuxt-asset-hash D4, nuxt-meta-uuid D8,
  nuxt-buildid D9, nuxt-cssmod D15, nuxt-tz-span D16 (recorded region truncated mid-tag;
  documented in citation note), nuxt-tz-jil D13, nuxt-tz-b D14 — all yunyuyuan/nuxt3-blog
  (commits 40b7bb516071 / a28de421d25f / f50767bf05e4)
- alex-present-time: alexcarpenter D1 (region stores literal \n escapes; pattern verified to
  match after unescaping; documented in citation note)
- beeps-og-timestamp: beeps D2
- cubxxw-hp-date: cubxxw D3 (e302344a57a8)
- godruoyi-time-tz: godruoyi D1 (b5bebb21bad5); godruoyi-pubdate: godruoyi D2 (2a505c3d70af)
- madrilene-time-display: madrilene D3 (5c24158e6c6a); feed-updated: madrilene D1;
  sitemap-lastmod: madrilene D2 + rimzzlabs D1 (328e90f173aa)
- opml-datecreated: cubxxw D2 (7090d6acbb75)

## Withdrawals (9)

C2 (generated content; site reclassified live_data/other): nemanjam-image-suffix,
nemanjam-excerpt-tail, nemanjam-island-uid, nemanjam-more-posts (also C3: no cited region),
nemanjam-hoisted-js — full; shiki-unwrap — scoped to nemanjam only (active for
alexcarpenter + rimzzlabs).
C3 (no citable recorded difference): category-page-num-mask, beeps-redaction-mask, nuxt-tz-bare.

## Validation (all passed 2026-09-26)

- parsed all 16 touched JSON files;
- every active rules.json entry has a non-empty derived_from list with
  site/commit/file/difference_id/region_before/region_after;
- no withdrawn rule id remains in rules.json; shiki-unwrap scoped correctly;
- rules-history.json: 9 withdrawal entries, final_rule_count=22;
- summary b1_b3/b1_b4 per-commit values exactly equal evaluation/<site>.json
  (missing_keep carried verbatim);
- summary nemanjam: reproducible=false, rules=[];
- nemanjam differences: 2 entries cause=live_data, other="generated content";
- `git diff --check`: clean (no whitespace errors);
- `git status --short`: no commit made; nothing pushed.
