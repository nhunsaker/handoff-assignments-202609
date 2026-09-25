# Assignment 20: how much of a page's geometry depends on fonts, images, scripts and third parties

Budget **12–16 hours**. The same HTML and CSS can render differently depending on whether a web font loaded, whether
an image had known dimensions, whether a script ran, and whether a third-party embed answered. This assignment
measures those dependencies on 40 real pages, and separately measures how much two identical renders differ from
each other, so that run-to-run noise can be told apart from real change.

## Phase 0 — Environment and pages

Rendering settings as assignment 14 Phase 0, Chromium, 1280×800. Pages: the 40 pages of assignment 15 Phase 0
(same selection rule, same three sites), plus 10 pages from other sites in assignment 08's probe list that embed
third-party content (a YouTube/Vimeo iframe, a tweet, a Mastodon embed, a map, a comments widget) — search the built
output for `<iframe`, `<script src="https://` and record what you found.

## Phase 1 — Conditions

Render each page under each condition, **from a fresh page load**, using Playwright request routing to block:

| id | condition |
|---|---|
| C0 | baseline: nothing blocked |
| C1 | **web fonts blocked**: abort requests whose resource type is `font` or whose URL matches `\.(woff2?|ttf|otf)(\?|$)` |
| C2 | **images blocked**: abort `image` requests (the `<img>` elements remain, with whatever `width`/`height` they declare) |
| C3 | **scripts disabled**: `javaScriptEnabled: false` |
| C4 | **third-party origins blocked**: abort every request whose origin differs from the page's |
| C5 | **all of C1–C4** |
| R1–R5 | five more **baseline** renders, fresh load each, for run-to-run noise |

Per render record the geometry of every body element (assignment 14 schema) and: number of requests, blocked
requests, `document.fonts.check` result for the body font, images with and without `width`/`height` attributes,
iframes and their sizes.

## Phase 2 — Measure

For C1–C5, per page: elements whose box differs from C0 by > 0.5 px in any of x/y/w/h; the count, the max `|dy|`,
the document-height difference; and the **first** differing element in document order (path, tag, class). For
C1 specifically, also the per-element `dh` distribution for text elements (`p`, `li`, `h1`–`h3`).

For R1–R5, per page: elements whose box differs from C0 in **any** run; if any, the element and the range of values
seen across the six baseline renders, and — from the page — the likely cause (a carousel, an animation, a live
widget, a lazy-loaded block, a randomized element); quote the markup or script that makes it vary.

## Output

```
output/
  environment.json
  pages.json          the 50 pages, what third-party content each embeds
  boxes/<site>/<page>/<condition>.json.gz          full geometry per render (cap 120 MB; summary rows survive the cap)
  results/<site>/<page>.json                       Phase 2 per page
  summary.json        per condition: pages affected, median/max elements affected, median document-height delta;
                      per page: whether any run-to-run jitter, and its cause; pages that failed to render
```

## Check-ins and review

This assignment follows the repository's **check-in, self-check and review protocol** (README, "Check-ins,
self-check and review"): push `output/` at every phase boundary and at least every 2 hours with an updated
`PROGRESS.md`; before the final commit, append the return manifest and re-derive every `summary.json` number from
the returned files; after the final commit, watch for `REVIEW.md` with `status: corrections_requested` and address
every numbered item in a new commit.

## Rules
- **Every number from a real render** under the stated condition; record what was actually blocked (count of aborted requests) so a condition that blocked nothing is visible.
- **Jitter is reported with its cause quoted from the page**, or `cause: unknown` — never omitted.
- **`summary.json` must be recomputable from the other files.**
- Write files as pages finish. No analysis or recommendations. Return the files.
