# Assignment 20: how list pages are built and what a new post does to them, across 30 real sites

**Phase:** P2 · P3 (see the README's phase tags)

Budget **12–16 hours**. A content site's list pages (post index, tag pages, archives, paginated lists) are where a
new post shows up without anyone editing that page. This assignment documents, for 30 real sites, how those pages
are put together in the built output and — by building two real commits where a post was added — exactly what the
addition changed, including whether an item crossed from one page of a paginated list to the next.

## Phase 0 — Sites

Take every site with a verdict of `capturable`, `corpus_ready` or `corpus_ready_normalizable` in assignments 08, 09
and 12 (if 12 has returned), then fill to **30** with your own GitHub search using assignment 12's Phase 1 queries
and its intake rules. At least 5 sites per framework where possible: Hugo, Jekyll, Eleventy, Astro, and one of
Next/Nuxt/SvelteKit/Gatsby. Build each at HEAD with the toolchain rules of assignment 10. List them in `sites.json`
with the build result; a site that does not build at HEAD is replaced, and the failure recorded.

## Phase 1 — List-page anatomy at HEAD

For each site, from the **built output**, identify every list page: the post index, tag and category pages, year and
month archives, paginated pages, feeds (`*.xml`, `*.json`). For each kind, record:

- `path` pattern (e.g. `blog/page/2/index.html`, `tags/<tag>/index.html`);
- the **container markup**: the CSS path of the element holding the items, the item tag, whether items are same-tag
  siblings, and the depth from item to the link that points at the content page;
- `items_per_page` and whether pagination exists (quote the config line that sets it, e.g. Jekyll `paginate: 10`,
  Hugo `paginate = 10`, Eleventy `pagination: size: 10`, Astro `paginate(posts, { pageSize: 10 })`);
- **sort order** (quote the template line) and therefore where a new post lands: `top`, `bottom`, `by_date_desc`, …;
- whether the item shows a date, an excerpt, a reading time, tags — anything that can change without the post changing;
- for the home page: whether it embeds the N latest posts (a list page in disguise) and N.

`anatomy/<owner>__<repo>.json`.

## Phase 2 — Two commits where a post was added

For each site, find in its history (last 24 months, first-parent) **one commit that adds exactly one new content
file** and its parent. Quote the added file's path and front matter (date, tags/categories). Build both. Then, from
the built outputs:

- **build each of the two commits twice first**; a list page whose body differs between the two builds of the same
  commit has nondeterministic order — report it as such and do not attribute its changes to the post;
- every page whose `<body>` hash changed (README **Page hashes**) — list them and classify each as
  `new_post_page`, `post_index`, `tag_page`, `category_page`, `archive_page`, `paginated_page_N`, `home`, `feed`,
  `other` (say what);
- for each changed list page: the container's item count before and after, the position of the new item, and
  **which existing items moved** (by their link target);
- **pagination crossings**: for paginated lists, whether the last item of page N before the commit is the first
  item of page N+1 after it — list every crossing (page N → page N+1, item link);
- for tag/category pages: which of the new post's tags gained an item, and whether any **new list page** was
  created (a first-time tag).

`additions/<owner>__<repo>.json`.

## Output

```
output/
  environment.json
  sites.json
  anatomy/<owner>__<repo>.json
  additions/<owner>__<repo>.json
  summary.json      sites built; per framework: container tag distribution, items-per-page distribution, sort
                    orders, sites with pagination; per addition: pages changed (median, by class), crossings found,
                    new tag pages created; sites where no post-adding commit exists in 24 months
```

## Check-ins and review

This assignment follows the repository's **check-in, self-check and review protocol** (README, "Check-ins,
self-check and review"): push `output/` at every phase boundary and at least every 2 hours with an updated
`PROGRESS.md`; before the final commit, append the return manifest and re-derive every `summary.json` number from
the returned files; after the final commit, watch for `REVIEW.md` with `status: corrections_requested` and address
every numbered item in a new commit.

## Rules
- **Quote template and config lines.** "It sorts by date" without the line is not a finding.
- **Every "changed page" comes from comparing two builds you ran.**
- **Environment failures are recorded as such.**
- **`summary.json` must be recomputable from the other files.**
- Write files as sites finish. No analysis or recommendations. Return the files.
