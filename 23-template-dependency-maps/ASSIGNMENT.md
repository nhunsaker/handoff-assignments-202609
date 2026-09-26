# Assignment 23: which pages each template, layout and partial reaches — mapped and checked against history

**Phase:** P3 (see the README's phase tags)

Budget **12–16 hours**. In a static site, one layout or partial (a header, a post card, a footer, a pagination
control) is rendered into many pages. Editing it changes all of them. This assignment maps every template to the
pages it reaches, from the built output, for the three corpus sites — and then checks the map against the real
history: when a commit touched a template, did exactly the mapped pages change?

## Phase 0 — Sites and templates

tempertemper (Eleventy), efcl (Jekyll), alexcarpenter (Astro), at their latest window commit (toolchain from 10).
From the **source**, list every template-like file: Eleventy layouts/includes (`_includes/`, `_layouts/`, `.njk`,
`.liquid`, `.webc`, `.11ty.js`), Jekyll `_layouts/` and `_includes/`, Astro `src/layouts/` and `src/components/`
(`.astro`), plus data files that feed templates (`_data/`, `src/data/`, `src/_data/`). For each: path, kind
(`layout | include | component | data`), and which other templates include it (quote the include/import line).
`templates/<site>.json`.

## Phase 1 — Map templates to pages from the built output

For each template, find its **rendered fingerprint**: build the site once, then build it again with the template
minimally changed (insert a harmless attribute `data-t22="<template id>"` on its root element, or for data files
change one value) and diff the built pages — every page that changed is reached by that template. **Diff by the
README's `body` hash, against a baseline:** build the site twice unmarked first; any page whose body differs between
those two builds is noise and is excluded from every template's reach (report it). A marker in a template or data
file that only reaches `<head>` (titles, meta, cache-buster) will not move the body hash: for those, also compare
the `normalized` hash and report head-only reach separately. Never use raw hashes here — on sites that stamp
`Date.now()` into every page, every template would appear to reach every page. **Revert between
templates**; one template per build. That is one build per template: ~30–80 builds per site, cheap for tempertemper,
minutes each for the others. Record per template the list of pages reached and the count.

Where a marker cannot be inserted (a data file, a template with no element root), say how you established the
mapping instead, or mark it `unmapped` with the reason.

`map/<site>.json`: template → pages, and the inverse, page → templates.

## Phase 2 — Check the map against history

From `10-build-history-diffs/output/pairs/<site>.json`: every pair whose `source_files_changed` includes at least one
template or data file from Phase 0 **and no content file** (no `*.md`, no `content/`, no `_posts/`, no `src/pages/**`
content). For each such pair, the mapped set = union of the pages mapped to the changed templates (at the map's
commit; note when the template did not exist yet). The changed set = pages whose `<body>` changed per 10's
`structure/` rows (plus pages whose inline `<style>` changed, listed separately). Report, per pair: mapped,
changed, `changed − mapped` (pages the map missed), `mapped − changed` (pages that did not change although mapped),
and — for each missed page — the reason if you can find it by looking at the diff of that page (quote it).

`history/<site>.json`.

## Output

```
output/
  environment.json
  templates/<site>.json
  map/<site>.json
  history/<site>.json
  summary.json      per site: templates listed, mapped, unmapped (with reasons); pages per template (median, max);
                    templates reaching every page; history pairs checked; exact-match rate; missed pages with reasons
```

## Check-ins and review

This assignment follows the repository's **check-in, self-check and review protocol** (README, "Check-ins,
self-check and review"): push `output/` at every phase boundary and at least every 2 hours with an updated
`PROGRESS.md`; before the final commit, append the return manifest and re-derive every `summary.json` number from
the returned files; after the final commit, watch for `REVIEW.md` with `status: corrections_requested` and address
every numbered item in a new commit.

## Rules
- **Every mapping comes from a build you ran with a marker**, not from reading the templates.
- **`mapped − changed` is a finding, not a defect to hide** — report it with the pages.
- **`summary.json` must be recomputable from the other files.**
- Write files as sites finish. No analysis or recommendations. Return the files.
