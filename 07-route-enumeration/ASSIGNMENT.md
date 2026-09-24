# Assignment 07: count a site's pages correctly, then re-probe two repositories where the count broke

Budget **8–12 hours**. Two halves: a per-framework rule that is verified rather than guessed,
then applying it to fix a result from Assignment 04 that was wrong because the counting was.

## Why this exists

Assignment 04 counted routes in build output and got it wrong for most frameworks: a site with
85 pages at HEAD was reported as **1 route**, and Astro and Next.js builds were reported as **0**.
Only Eleventy produced a believable number. Every downstream figure that multiplied by route
count is therefore meaningless. This assignment makes the count right and then re-derives those
figures.

You may clone repositories and run builds. Nothing will be uploaded to you.

---

## Phase 0 — Environment (20 min)

Node 20/22, npm, pnpm, git, Hugo binary, Python 3 for MkDocs. Reuse the date-matched toolchain
ladder from Assignment 04. Record in `environment.json`.

---

## Phase 1 — The route-enumeration rule, per framework (~40 min each)

For each framework starter from Assignment 05 — Eleventy, Astro, Docusaurus, VitePress, Hugo,
Jekyll, MkDocs, Nuxt — plus **Next.js (`next build` static export) and Vite+React**, which
Assignment 05 did not cover:

1. Build the starter.
2. Enumerate the build output and determine the exact mapping from output file to URL. Record
   the output directory, which file patterns are pages (and which are **not** — asset chunks,
   `404.html`, pagination duplicates, `index.html` vs `foo/index.html` vs `foo.html`), and how a
   file path becomes a route.
3. **Verify against a second source of truth:** the framework's own sitemap if it emits one,
   its dev-server route list, its build log ("N pages generated"), or a hand count of the
   starter's source pages. The count from your rule must match that source. If it does not,
   the rule is wrong; say what the discrepancy was and fix the rule.
4. Add **three pages** to the starter (a top-level page, a nested page, a dynamic/collection
   page if the framework has the concept), rebuild, and confirm your rule's count rises by
   exactly three.

`output/route_rules/<framework>.json`:

```json
{
  "framework": "", "version_tested": "",
  "output_dir": "dist/",
  "page_file_patterns": ["**/index.html"],
  "excluded_patterns": ["404.html", "_astro/**"],
  "file_to_url": "strip output_dir, strip trailing index.html, ensure leading slash",
  "second_source_of_truth": "sitemap.xml | build log | dev route list | hand count",
  "starter_count_by_rule": 0, "starter_count_by_truth": 0, "matched": true,
  "plus_three_pages_count": 0, "delta_was_exactly_three": true,
  "gotchas": ["every case where the obvious rule was wrong, in one line each"]
}
```

**`gotchas` is the field I care about most.** Next.js app-router output, Astro's `_astro/`
chunks, Hugo's taxonomy pages, Docusaurus's versioned docs — each has a trap, and the trap is
what I cannot learn from the docs.

---

## Phase 2 — Re-count Assignment 04's buildable commits (~2 h)

Apply the verified rules to the buildable commits from Assignment 04's manifests:

- `midudev/jsconf.es` — all 146 buildable commits (Astro)
- `mrsibe/KnowNote` — the 41 buildable (Vite+React)
- `11ty/eleventy-base-blog` — the 5 (Eleventy; should reproduce 13)

Write `output/recount/<repo>.json` with per-commit `route_count` and `route_count_method`, plus
`route_count_min/median/max` and the corrected **`expected_page_commit_pairs`** =
`build_ok × route_count_median`. Then `output/recount/summary.json` ranking the repositories by
that figure — the ranking Assignment 04 could not produce.

---

## Phase 3 — Re-probe two repositories in a RECENT window (~3 h)

Assignment 04 chose each repository's densest six-month window of page-touching commits. For
two repositories that rule chose windows from **2020**, five years old, so their build results
describe ancient commits rather than the repository as it exists now:

| repo | Assignment 04 window | result |
|---|---|---|
| `vercel/commerce` | 2020-09 → 2021-02 | installed 147/150, built 0 |
| `leerob/leerob.io` | 2020-02 → 2020-07 | 23/61, 35 timeouts |

Re-probe each in its **most recent six months that contain at least 20 page-touching commits**,
the same way as Assignment 04 (date-matched toolchain, every commit, 300 s cap) — but **start
with six evenly-spaced commits**, and only probe the full window if at least 4 of 6 build.
Apply the Phase 1 route rule for Next.js so the count is right this time.

`output/recent_reprobe/<repo>.json` in the Assignment 04 manifest format, plus
`output/recent_reprobe/summary.json` answering, for each repo: does it build in its recent
history, at what rate, with what route count — and how does that compare to the 2020 window.

---

## Rules

- **A rule that fails its second-source check is not a rule.** Do not report a count your own
  verification contradicted.
- **Report per-commit counts, not just the median.** A repository whose route count swings from
  1 to 85 across its window is telling me something.
- **Environment failures are `environment`**, never `build`. Same discipline as 04.
- **Write each framework's rule and each repo's recount as it finishes.**
- No analysis or recommendations. Return the files.
