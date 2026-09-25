# Assignment 21: every CSS change in three sites' histories, at the declaration level

Budget **12–16 hours**. Assignment 10 recorded which commits changed a stylesheet. This assignment records **what**
changed: every added, removed and modified declaration in the **built** CSS between consecutive commits, with its
selector and property, classified by kind — and pairs it with the pages whose bodies changed in the same commit.

## Phase 0 — Commits

From `10-build-history-diffs/output/pairs/*.json`, every pair where `assets_modified`, `assets_added` or
`assets_removed` includes a `.css` file, **or** `source_files_changed` includes `*.css`, `*.scss`, `*.sass`, `*.less`,
`*.pcss` or `tailwind.config.*`. Build both commits of each pair (toolchain from 10's probes). Expect roughly 40–80
pairs across tempertemper, efcl and alexcarpenter; list them in `pairs.json`.

## Phase 1 — Declaration diff

For each pair, parse every built CSS file (and every inline `<style>` block on each page — tempertemper inlines its
critical CSS; treat each page's inline block as a file named by the page) with a real CSS parser (`postcss` or
Python `tinycss2`; name it). Normalize: minified and unminified must compare equal — compare parsed rules, not
text. Then diff:

```json
{ "file": "assets/css/main.css", "selector": ".header nav ul li + li", "at_rule": "@media (min-width: 60em)",
  "property": "margin-left", "before": ".5em", "after": "1em", "change": "modified" }
```

`change` ∈ `added_rule | removed_rule | added_declaration | removed_declaration | modified`. Selectors are recorded
verbatim; `at_rule` is the enclosing at-rule chain or null. Also record per pair: rules and declarations counted
before/after, and the number of changes.

## Phase 2 — Classify

Every change gets a `kind` from its property: `color` (color, background-color, border-color, fill, stroke,
opacity), `typography` (font-*, line-height, letter-spacing, text-*, hyphens, word-*), `spacing` (margin-*,
padding-*, gap, row-gap, column-gap), `size` (width, height, min-*, max-*, flex-basis, aspect-ratio), `layout_mode`
(display, position, float, flex-*, grid-*, align-*, justify-*, order, columns), `box` (border-width, box-sizing,
overflow, contain), `visual_only` (border-radius, box-shadow, transform, transition, animation, cursor, outline,
filter), `custom_property` (`--*`), `other` (name it). A `@media` change that wraps otherwise identical declarations
is `media_query`. Record the mapping you used in `kinds.json` so it can be checked.

## Phase 3 — Pair with the page changes

For each pair, from 10's `structure/` rows: the pages whose `<body>` changed and the count of sibling-group, text-only
and attribute-only changes on them. Note that a pure-CSS commit changing an inline critical-CSS block changes the
`<head>`, not the `<body>`; record separately the pages whose inline `<style>` changed. Output
`pairs/<site>/<from12>__<to12>.json` holding Phases 1–3 for that pair.

## Output

```
output/
  environment.json
  pairs.json
  kinds.json
  pairs/<site>/<from12>__<to12>.json
  summary.json      per site: pairs, total changes by `change` and by `kind`, the 20 most-changed selectors, the
                    20 most-changed properties, how many pairs changed only `color`/`visual_only`, how many changed
                    `layout_mode`/`size`/`spacing`; per pair the counts
```

## Check-ins and review

This assignment follows the repository's **check-in, self-check and review protocol** (README, "Check-ins,
self-check and review"): push `output/` at every phase boundary and at least every 2 hours with an updated
`PROGRESS.md`; before the final commit, append the return manifest and re-derive every `summary.json` number from
the returned files; after the final commit, watch for `REVIEW.md` with `status: corrections_requested` and address
every numbered item in a new commit.

## Rules
- **Diffs come from parsed rules of two builds you ran**, never from the source diff (source SCSS is not what the
  browser sees).
- **Parser failures are recorded per file**, with the error, not skipped.
- **`summary.json` must be recomputable from the other files.**
- Write files as pairs finish. No analysis or recommendations. Return the files.
