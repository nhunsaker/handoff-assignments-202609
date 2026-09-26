status: corrections_requested
round: 2
verified: tempertemper's b1==b2 raw identity at 06f96f7861a6 checked against source — at that commit the cache-buster is `?v={{ site.version }}` (deterministic); by 60daa0f63 (2025-12-29) it is `Date.now()` in eleventy/index.js, so the non-determinism entered mid-window, exactly as the data shows. b3 (timezone/locale) and b4 (fresh install) comparisons are present in evaluation/<site>.json for every site. Rules are data, scoped per site, with causes.
corrections:
  - C1: Signal retention was measured per PAGE ("N/N pages differ before and after; 0 became identical"). That cannot detect a rule that erases a real change INSIDE a page that also differs elsewhere. For every rule, measure it per REGION: on the signal pair's two builds, extract every region the rule matches in both versions and report how many matched regions DIFFER between the two commits (i.e. real change the rule would hide). Add `regions_matched`, `regions_differing_across_commits`, and up to 5 verbatim examples per rule to evaluation/signal_<site>.json. A rule with any differing region across commits is `signal_lost: true`.
  - C2: `nemanjam/nemanjam.github.io` is not a content site: its posts are generated placeholder text ("Dolor velit excepteur cupidatat…") that changes on every build, and 52 page paths exist only in one build of the same commit (differences file, commit 6333be10bf83). Masking that is not normalization. Re-classify it `live_data`/`other: generated content` with the quote, mark the site non-reproducible in summary.json, and move its six rules to rules-history.json as withdrawn.
  - C3: `nemanjam-more-posts` has no difference in differences/nemanjam__nemanjam.github.io.json that it was derived from (no region mentions "More posts"). Every rule must cite the difference it removes: add a `derived_from` field to every rule in rules.json (site, commit, file, and the verbatim region), and withdraw any rule that cannot cite one.
  - C4: summary.json reports only b1↔b2. Add the b1↔b3 and b1↔b4 before/after counts per site (they are in evaluation/<site>.json already; this is a summary-only change).
  - C5: No PROGRESS.md (README protocol). Add one with the return manifest and the recompute statement.

## Round 2 (2026-09-26) — one correction left, and it is partly our specification's fault
Accepted: C2 (nemanjam reclassified generated content, non-reproducible, its rules withdrawn), C3 (derived_from on
every surviving rule; 30 → 22 active), C4 (b1↔b3 and b1↔b4 in summary.json), C5 (PROGRESS.md). The one-rule-at-a-time
check that withdrawals flip no page equality is exactly right.
corrections:
  - C1-R2: Round 1's C1 asked for regions that differ between the two COMMITS. That definition flags every rule that
    strips per-build noise (a build id, a timestamp, a random class suffix differs between any two builds, so it
    differs between commits too) — hence beeps cache-buster-q 2646/2646 and the six nuxt rules. Refine: a region is
    hidden SIGNAL only if it differs between the two commits AND is IDENTICAL between two builds (b1, b2) of each
    commit. Using the retained build dirs, for every rule with regions_differing_across_commits > 0 report
    `regions_hidden_signal` (differs across commits, stable across builds) and `regions_hidden_noise` (varies across
    builds), recompute signal_lost from the first, and give up to 5 verbatim examples of hidden signal. Most
    important: `shiki-unwrap` on alexcarpenter (205) and rimzzlabs (254) — token colours genuinely change between
    commits (e.g. `color:#0550AE` → `#CF222E` on notes/1/index.html); if shiki colours are stable across builds of
    the same commit, the rule hides real visual change and must be narrowed (e.g. keep the style attribute, unwrap
    nothing) or withdrawn. madrilene-time-display's 2 regions are a trailing space in the date text; note, no action.
