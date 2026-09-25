# Assignment 16: the rendered geometry of every changed page across tempertemper's history

Budget **16–24 hours**. Assignments 10 and 11 give, for each of tempertemper's 102 commits, which built pages
changed. This assignment **renders** each changed page at each commit and records the geometry of every element,
so that the history can be read as "what moved, commit by commit" rather than "what markup changed".

## Phase 0 — Environment

The README's **Shared rendering settings**, **Chromium only**, at **two viewports**: 1280×800 and 390×844.
Toolchain per commit as recorded in `10-build-history-diffs/output/probes/tempertemper__www.tempertemper.net.json`.

## Phase 1 — Which pages to render

For each commit in order (102, from 10's `commits/` file): build it. Decide the page set:

- **Commit 1:** every page.
- **Each later commit:** every page whose `<body>` hash differs from the previous **built** commit. If
  `11-manifests-normalized/output/manifests/` exists, use its `body` hashes; otherwise compute the body hash yourself
  the way assignment 11 defines it (`lxml.html`, `tostring(body, method="html", encoding="unicode")`, sha256).
  **Plus**, at every commit regardless: `index.html`, `blog/index.html`, `blog/year/*.html`, `category/*.html`
  (so the list pages have an unbroken series).

Record the page set and the reason for each page in `pages/<sha12>.json`.

## Phase 2 — Render and record

For each (commit, page, viewport): serve the built output, load the page, and record every element under
`<body>`:

```json
{ "path": "html > body > div:nth-of-type(1) > main:nth-of-type(1) > ol:nth-of-type(1) > li:nth-of-type(3)",
  "tag": "li", "id": null, "class": "post", "attrs": { "data-year": "2025" },
  "text_sha": "…", "text_len": 84, "child_count": 2,
  "x": 120.5, "y": 1834.25, "w": 640, "h": 96.5,
  "display": "list-item", "position": "static" }
```

`attrs` holds every attribute except `class`, `id`, `style` (which have their own fields or are omitted), with
values truncated to 200 characters. `display` and `position` come from `getComputedStyle`. Also record per page:
document height, the count of elements, whether `document.fonts.ready` resolved with the site's web font loaded
(`document.fonts.check` on the body font), and the load time.

Write `geometry/<sha12>/<viewport>/<page path with / as __>.json.gz` — **one file per page, gzipped**. Expected
volume: ~2,000 page renders × ~600 elements × 2 viewports; keep the whole `geometry/` tree under **180 MB**. If it
would exceed that, drop `attrs` first, then the 390-wide viewport for non-list pages, and say exactly what was
dropped in `summary.json`.

## Phase 3 — Consecutive-pair deltas for the list pages

For `index.html`, `blog/index.html`, `blog/year/*.html` and `category/*.html` only, for each consecutive pair of
commits, at 1280×800: match elements across the pair by **(tag, text_sha, parent's tag+text_sha)** — say so in the
file — and record per matched element `dx, dy, dw, dh`; unmatched elements on either side are listed as such. Output
`deltas/<from12>__<to12>/<page>.json`. This is a convenience view; the geometry files are the record.

## Output

```
output/
  environment.json
  pages/<sha12>.json
  geometry/<sha12>/<1280x800|390x844>/<page>.json.gz
  deltas/<from12>__<to12>/<page>.json
  summary.json      commits built, pages rendered per commit (min/median/max), total elements recorded,
                    renders that failed (page, commit, error), font-loaded rate, size of geometry/, anything dropped
```

## Check-ins and review

This assignment follows the repository's **check-in, self-check and review protocol** (README, "Check-ins,
self-check and review"): push `output/` at every phase boundary and at least every 2 hours with an updated
`PROGRESS.md`; before the final commit, append the return manifest and re-derive every `summary.json` number from
the returned files; after the final commit, watch for `REVIEW.md` with `status: corrections_requested` and address
every numbered item in a new commit.

## Rules
- **Never report geometry you did not render.** No interpolation between commits.
- **A failed render is a row in `summary.json`**, not a missing file nobody mentions.
- **`summary.json` must be recomputable from the other files.**
- Write files as commits finish; the order is the commit order. No analysis or recommendations. Return the files.
