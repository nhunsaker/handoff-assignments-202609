# Assignment 18: what a content edit does to the geometry of a real page

**Phase:** P1 · P3 (see the README's phase tags)

Budget **14–18 hours**. Assignment 21 measures single CSS changes on minimal pages. This one measures **content
edits on real built pages**: insert a list item, remove one, lengthen a heading, add a paragraph, add an image — the
edits a site's history is made of — and records exactly which elements moved, by how much, how far the effect
travelled, and what stopped it.

## Phase 0 — Environment and pages

The README's **Shared rendering settings**, **Chromium only**, at **three viewports**: 1280×800, 768×1024,
390×844. Build the three sites from assignment 10 at their latest commit in the window (tempertemper, efcl,
alexcarpenter). Choose **40 pages**: for each site, its post index, two tag/category pages, one year archive, five
posts, and the home page (fewer if a site lacks a kind; say so). Serve each site's built output locally.

## Phase 1 — The edit catalogue

Apply each edit **in the live DOM before measuring** (a Playwright `page.evaluate` that mutates the DOM; then wait
one `requestAnimationFrame` and measure). Never edit source; every experiment starts from a fresh load of the
unmodified page. Edits, each defined precisely:

| id | edit | where |
|---|---|---|
| E1 | **insert** a clone of an existing sibling at position 0 of a sibling group | every sibling group with ≥ 3 same-tag children (cap 12 groups per page, largest first) |
| E2 | insert the same clone at the **middle** | same groups |
| E3 | insert at the **end** | same groups |
| E4 | **remove** the first member | same groups |
| E5 | **lengthen text**: append 20 / 100 / 400 characters of real words (taken from the same page) to a text node | every `h1`–`h3`, and the first 5 `p` and 5 `li` |
| E6 | **shorten text** to its first 3 words | same elements as E5 |
| E7 | **add a paragraph** (60 words) immediately after the element | every `h1`–`h3`, first 5 `p` |
| E8 | **add an image** 800×450 with `width`/`height` attributes set | after the first `p` in `main`, and inside the first `li` of the largest group |
| E9 | the same image **without** `width`/`height`, `src` pointing at a local 800×450 PNG you serve | same places |
| E10 | **wrap** the element's text in `<strong>` (no size change expected) | first 5 `p` |

Roughly 40 pages × ~60 edits × 3 viewports ≈ 7,000 renders. At ~0.5 s each that is an hour of rendering; the budget
is in the bookkeeping.

## Phase 2 — Measure

Per experiment: geometry of every body element before and after (same schema as 14), then:

- per element: `dx`, `dy`, `dw`, `dh`, and the class `unchanged | moved | resized | moved_and_resized`;
- **reach**: the number of elements moved; the furthest moved element by DOM distance (edges in the tree from the
  edited element) and by pixels; whether the page's total height changed and by how much;
- **stoppers**: for every ancestor of the edited element, whether elements *after* that ancestor moved. The nearest
  ancestor after which nothing moved is the stopper; record its tag, classes, and — via `getComputedStyle` — its
  `height`, `min-height`, `max-height`, `overflow`, `position`, `display`, `contain`, and for grid parents
  `grid-template-rows`. If nothing stopped it, `stopper: null`.

Output `experiments/<site>/<page>.json`: one row per (edit, target, viewport) with all of the above. Full per-element
boxes go to `boxes/<site>/<page>/<experiment id>.json.gz` (gzip; cap the whole `boxes/` tree at **150 MB** — beyond
that keep the summary rows only and say where the cap hit).

## Phase 3 — Roll-up

`summary.json`: per site and per edit kind: experiments run; distribution of elements moved (0 / 1–5 / 6–20 / 21–100
/ 100+); median and max reach in pixels and in DOM edges; how often the page height changed; stoppers found, counted
by the computed-style property that appears to explain them; and, for E8 vs E9, the difference the `width`/`height`
attributes made. Also list every experiment where **an element before the edit point in document order** moved — with
the page, edit and element — because that is not expected in normal flow.

## Check-ins and review

This assignment follows the repository's **check-in, self-check and review protocol** (README, "Check-ins,
self-check and review"): push `output/` at every phase boundary and at least every 2 hours with an updated
`PROGRESS.md`; before the final commit, append the return manifest and re-derive every `summary.json` number from
the returned files; after the final commit, watch for `REVIEW.md` with `status: corrections_requested` and address
every numbered item in a new commit.

## Rules
- **Never report a measurement you did not take.** All boxes from real renders after a real DOM mutation.
- **A fresh page load per experiment.** No experiment inherits another's mutation.
- **Environment failures recorded as such.** Pages that fail to render are listed, not skipped silently.
- **`summary.json` must be recomputable from the other files.**
- Write files as pages finish. No analysis or recommendations. Return the files.
