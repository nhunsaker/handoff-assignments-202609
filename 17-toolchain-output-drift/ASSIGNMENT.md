# Assignment 17: how much a site's built output depends on the toolchain version

**Phase:** P1 · P2 (see the README's phase tags)

Budget **12–16 hours**. Assignments 02 and 10 built old commits under a **date-matched** toolchain (the framework
and Node version current at the commit's date). That is slow to set up. If building under today's versions gives the
same pages, the date-matching is wasted effort; if it gives different pages, the differences matter. This assignment
measures it.

## Phase 0 — Sites and commits

Six sites, three commits each (earliest, middle, latest successful build in the window from the earlier
assignment): tempertemper (Eleventy), madrilene/lenesaile.com (Eleventy), efcl (Jekyll), cubxxw/blog (Hugo),
alexcarpenter (Astro), godruoyi/gblog (Astro). Windows and date-matched toolchains from assignments 08 and 10.

## Phase 1 — Three toolchains per commit

| id | toolchain |
|---|---|
| T1 | **date-matched**, exactly as the earlier assignment recorded it |
| T2 | **latest**: the newest framework version that installs and builds today (bump only the framework and its official plugins in a throwaway copy of `package.json`/`Gemfile`/Hugo binary; keep the site's own code untouched; record every version changed) |
| T3 | **oldest allowed**: the oldest framework version that satisfies the site's declared range at that commit |

For Hugo, T2/T3 are Hugo binaries; for Jekyll, gem versions in a throwaway Gemfile; for Node frameworks, package
versions with the lockfile regenerated in the throwaway copy. If a toolchain will not install or build, record the
failure verbatim (five lines) and move on — that is a result.

## Phase 2 — Compare outputs

For every (commit, T1 vs T2) and (commit, T1 vs T3): per built page, three hashes — raw, normalized (assignment 11's
rules, plus assignment 13's `rules.json` if it has returned; say which), and `<body>` (assignment 11's definition).
Report pages identical/different under each hash. For pages whose **body** differs, classify the difference by
parsing both with `lxml.html` and diffing: `whitespace_only`, `attribute_order`, `attribute_value` (which
attributes), `element_added`/`element_removed` (which tags, how many), `text_changed`, `structure_changed` (describe).
Quote one region (±80 chars) per distinct kind per page.

Also diff the non-HTML assets: names (content hashes in filenames), CSS (a parsed-rule diff: parse both with `postcss` or `tinycss2` and compare rules, not text), JS
(size and hash only).

## Output

```
output/
  environment.json
  toolchains/<site>/<sha12>.json     versions used and the install/build result for T1, T2, T3
  manifests/<site>/<sha12>/<T1|T2|T3>.json    page → {raw, normalized, body}; assets → hash
  diffs/<site>/<sha12>/<T1-T2|T1-T3>.json
  summary.json      per site and per comparison: builds attempted/succeeded; pages identical by raw/normalized/body;
                    body differences by kind; the largest single difference quoted; versions changed
```

## Check-ins and review

This assignment follows the repository's **check-in, self-check and review protocol** (README, "Check-ins,
self-check and review"): push `output/` at every phase boundary and at least every 2 hours with an updated
`PROGRESS.md`; before the final commit, append the return manifest and re-derive every `summary.json` number from
the returned files; after the final commit, watch for `REVIEW.md` with `status: corrections_requested` and address
every numbered item in a new commit.

## Rules
- **Every hash from a build you ran.** No inference from changelogs.
- **Toolchain failures are results**, recorded verbatim.
- **`summary.json` must be recomputable from the other files.**
- Write files as commits finish. No analysis or recommendations. Return the files.
