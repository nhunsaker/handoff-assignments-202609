# Assignment 19: how text length turns into height — measured tables for real fonts

**Phase:** P1 · P3 (see the README's phase tags)

Budget **12–16 hours**. When text gets longer, the element gets taller, in steps of one line. Exactly when it steps
depends on the font, the size, the width, the line-height, hyphenation and wrapping rules. This assignment measures
those steps directly, for the fonts the three corpus sites actually use and for the system fonts, and returns the
tables.

## Phase 0 — Environment

The README's **Shared rendering settings**, Chromium and Firefox (WebKit too if you have it). Collect the fonts:

1. From the built output of tempertemper, efcl and alexcarpenter at their latest window commit: every `@font-face`
   in the built CSS (quote the rule) and the font files, served locally. Also every `font-family` stack used on
   body text and headings (from the built CSS, quoted).
2. System fonts available in the browser: `system-ui`, `sans-serif`, `serif`, `monospace`, and the resolved family
   name for each (read it from the computed style plus a canvas measurement of a test string, and say how you got
   it).

`fonts.json` lists every family with its source and whether it loaded (`document.fonts.check`).

## Phase 1 — The grid

For every (font family, font size, width, line-height, wrapping mode) in:

- sizes: 14, 16, 18, 20, 24, 32 px (and 48 px for headings);
- widths: 240 to 1200 px in steps of 40;
- line-height: `normal`, 1.4, 1.6;
- wrapping: default; `hyphens: auto` (with `lang="en"`); `overflow-wrap: anywhere`; `text-wrap: balance`;
  `text-wrap: pretty`; `white-space: pre-wrap`;

render a `<p>` (and for 32/48 px an `<h2>`) containing **real English text** (take paragraphs from the corpus sites'
built pages; record which) of length 1, 2, 3 … words up to 400 words, and record `getBoundingClientRect().height`
and the line count (`height / lineHeight` where line-height is known; otherwise count with `Range.getClientRects()`
and say so). **Do it incrementally in one page** — add a word, measure, repeat — so 400 measurements cost one load.

That is ~15 families × 7 sizes × 25 widths × 3 line-heights × 6 modes × 400 lengths ≈ 47 M measurements: too many.
Sample: run the **full** grid for three families (the body font of each site) at widths of 320, 640, 960; run all
widths at 16 px and 24 px with `normal` line-height and default wrapping; and run all wrapping modes at 16 px and
640 px. Record precisely which cells you ran in `grid.json`.

## Phase 2 — Derived tables

From the raw measurements, per cell: the word count and character count at which the line count first reaches
2, 3, 4 … (the "step points"); the mean characters per line; the variance of characters per line across steps
(how irregular wrapping is); and, comparing engines, whether the step points agree.

Also measure the **width at which a fixed text wraps to one more line**: for 30 fixed strings (headings from the
corpus), shrink the width 1 px at a time from 1200 to 240 and record every width at which the line count changes.

## Output

```
output/
  environment.json    browsers, fonts loaded, how family names were resolved
  fonts.json          every family, source, @font-face rule quoted
  grid.json           the cells actually measured
  raw/<family>/<size>-<width>-<lh>-<mode>.json.gz     length → height, line count
  steps.json          Phase 2 step points per cell
  width-steps.json    the 30 fixed strings and their wrap widths
  summary.json        cells measured, engine agreement rate on step points, families that failed to load
```

## Check-ins and review

This assignment follows the repository's **check-in, self-check and review protocol** (README, "Check-ins,
self-check and review"): push `output/` at every phase boundary and at least every 2 hours with an updated
`PROGRESS.md`; before the final commit, append the return manifest and re-derive every `summary.json` number from
the returned files; after the final commit, watch for `REVIEW.md` with `status: corrections_requested` and address
every numbered item in a new commit.

## Rules
- **Every number from a real render.** No estimation from average character widths.
- **Fonts that did not load are reported, not substituted silently**; the resolved family is recorded per cell.
- **`summary.json` must be recomputable from the other files.**
- Write files as cells finish. No analysis or recommendations. Return the files.
