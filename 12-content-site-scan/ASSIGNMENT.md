# Assignment 12: find content sites with index pages, whose history builds reproducibly

Budget **16–24 hours**. The biggest assignment in this repo. Assignment 08 screened 150 repositories and found one
site that clears every bar (three once the build-time limit was dropped, a fourth in 09). This scan uses everything
the last five scans learned to find **ten or more**, and adds two filters none of them had.

## What we want, precisely

A **content site** (a blog, a publication, a portfolio with a writing section, a changelog site) whose built output
includes **index pages that list other pages**: a post index, tag or category pages, year/month archives, a paginated
list. New content inserts items into those lists; the history of such a site is full of list insertions. Assignment
10 found that `tempertemper`'s `blog/index.html` gained one `<li>` at position 0 per new post, dozens of times in six
months. That is the pattern we want more of.

And its builds must be **reproducible**: the same commit built twice produces the same pages once trivially volatile
values are normalized.

You may clone repositories and run builds. Nothing will be uploaded to you.

---

## Phase 0 — Environment (20 min)

As assignment 10: Node through a version manager, corepack, npm/pnpm/yarn, **Ruby + Bundler**, **Hugo** (extended;
able to switch versions — Hugo sites pin versions in `netlify.toml`, `.hugo-version`, `hugo.toml`, CI files, or
`go.mod`), **Go** if a Hugo site uses modules, git, ≥ 60 GB free. Record in `environment.json` with registry checks.

## Phase 1 — Candidates (300)

GitHub search, **300 candidates**, stratified:

| bucket | framework | target |
|---|---|---|
| H | Hugo | 70 |
| E | Eleventy | 60 |
| J | Jekyll | 50 |
| A | Astro (static output) | 60 |
| N | Next.js with `output: 'export'`, Nuxt `generate`, SvelteKit with `adapter-static`, Gatsby | 60 |

Good queries search for **sites**, not starters: personal blogs, engineering blogs of small companies, newsletters,
publications, digital gardens; `topic:blog`, `topic:personal-website`, `path:content/posts`, `path:_posts`,
`path:src/posts` combined with a framework's config filename. Record every query in `searches.json`.

**Reject at intake, logging the reason:** framework-owned repos; themes, starters, templates, boilerplates, "demo"
sites; documentation for a developer tool; monorepos where the site is one package; no committed lockfile (Hugo and
Jekyll: `Gemfile.lock` for Jekyll; Hugo needs no lockfile but must pin a Hugo version somewhere — quote where);
**any repository already covered by assignments 01, 02, 04, 06, 08, 09 or 10** (list their names from those folders
and exclude them).

## Phase 2 — Static-output screen (no builds)

Exactly assignment 08's Phase 2, with these rules added from what has slipped through since:

- **SvelteKit passes only with `@sveltejs/adapter-static`.** `adapter-cloudflare`, `adapter-vercel`, `adapter-node`,
  `adapter-netlify` and `adapter-auto` are runtime adapters: reject, quoting the import line.
- **`output_mode: "unknown"` is not a pass.** If you cannot quote a line that makes the output static (or a framework
  whose output is static by construction: Hugo, Jekyll, Eleventy), reject with reason `output_mode_unproven`.
- Reject fewer than **20** source content pages (posts, articles, notes) at HEAD.

## Phase 3 — The index-page screen (new; no builds)

Read the source at HEAD and establish that the site **generates list pages**. Quote evidence per framework:

| framework | evidence |
|---|---|
| Hugo | a `list.html`, `section.html`, `taxonomy.html` or `term.html` layout, or `taxonomies` in config |
| Jekyll | `paginate` in `_config.yml`, `jekyll-archives`, or a page iterating `site.posts` |
| Eleventy | a template with `pagination:` over a collection, or iterating `collections.<name>` |
| Astro | `getStaticPaths` returning tag/category/page params, or a page calling `getCollection` and mapping the result |
| Next/Nuxt/Gatsby/SvelteKit | the equivalent listing route; quote the file and the line |

Record `index_page_evidence` (file + verbatim line) and `index_page_kinds` (`post_index`, `tag`, `category`,
`archive_year`, `paginated`). Reject with `no_index_pages` otherwise.

## Phase 4 — The build-time network screen (new; no builds)

Grep the source for build-time network access: `fetch(`, `axios`, `got(`, `EleventyFetch`, `getRemote`,
`resources.GetRemote` (Hugo), `http://`/`https://` inside data files (`_data/`, `src/data/`, `data/`), GraphQL
endpoints, CMS SDKs (Contentful, Sanity, Strapi, Notion, WordPress REST, Ghost). For each hit, quote the file and line
and classify: `build_time_fetch`, `client_side_only` (inside a `<script>` that runs in the browser), or
`not_network`. **Any `build_time_fetch` rejects the repository** with reason `build_time_fetch` — its pages depend on
a live service and cannot be rebuilt as they were. Record every hit even for passes.

## Phase 5 — Window

As 08 Phase 3: the six-month window with the most page-touching commits, ending no earlier than **24 months before
today**, `package.json` (or the framework's equivalent manifest) present at every commit, ≥ **25** page-touching
commits. Window dates are **start and end dates, both real**; do not label a window that runs past today.

**Plus:** at least **5** of the commits in the window must **add a new content file** (a new post). Count them;
list them. A site with churn but no new posts has no list insertions.

## Phase 6 — Build eight commits (the real test)

Eight commits evenly spaced across the window, **at least three of them commits that add a new content file**.
Per commit: clean worktree; toolchain rungs as assignment 10 (a range resolves to the newest satisfying release at
the commit's date, never the lowest; package manager from the lockfile via corepack; Ruby from `.ruby-version`; Hugo
from the pinned version); install; build; **count static pages** by the rules in assignment 07; quote the output
directory's config line.

Per commit also record the **list pages you can identify in the output** (paths of the post index, tag, archive
pages) and, for each, the count of links to content pages in its main list (parse with `lxml.html`; name the
selector you used and quote why it is the main list).

## Phase 7 — Reproducibility

For every repository that builds 8/8: rebuild **two** of the eight commits a second time in a fresh worktree with an
empty output directory, and compare every page. Compute a raw sha256 and a **body** sha256 (the `<body>` subtree
re-serialized by `lxml.html.tostring(body, method="html", encoding="unicode")`). Report per page whether each
differs. Where the body differs between two builds of the same commit, quote one differing region (±80
characters) per distinct cause.

### Verdicts

- **`corpus_ready`** — 8/8 build, median static pages ≥ 20, list pages present at every commit, and the two
  reproducibility rebuilds have **identical body hashes on every page**.
- **`corpus_ready_normalizable`** — as above, but body hashes differ between rebuilds **only** in regions you can
  quote as timestamps, build ids or cache-busting values.
- **`nondeterministic`** — builds, but body hashes differ between rebuilds for any other reason (reordering, random
  ids, content). Name the cause.
- **`no_list_insertions`** — builds, but no list page's main-list count changes across the eight commits.
- **`spa`**, **`broken`**, **`environment_incomplete`** — as assignment 08.

There is no build-time limit. Record median build seconds.

## Output

```
output/
  environment.json
  searches.json
  candidates.json          Phase 1, all 300, intake rejections with reasons
  screen.json              Phases 2–4, one row per candidate that passed intake, every quoted line
  windows.json             Phase 5, with new-content commit lists
  probes/<owner>__<repo>.json    Phase 6 per commit + Phase 7 rebuild comparison
  summary.json             funnel 300 → intake → static → index pages → no fetch → window → probed → verdicts,
                           per bucket; and the corpus_ready + corpus_ready_normalizable list ranked by
                           (median static pages × new-content commits in window)
```

## Check-ins and review

This assignment follows the repository's **check-in, self-check and review protocol** (README, "Check-ins,
self-check and review"): push `output/` at every phase boundary and at least every 2 hours with an updated
`PROGRESS.md`; before the final commit, append the return manifest and re-derive every `summary.json` number from
the returned files; after the final commit, watch for `REVIEW.md` with `status: corrections_requested` and address
every numbered item in a new commit.

## Rules
- **Quote config lines.** "It looked static" and "it has a blog" are not evidence.
- **Never report a build you did not run**, a page count or hash you did not compute from files on disk.
- **Verbatim error excerpts**, five real lines (or all the lines there were, saying so).
- **Environment failures are `environment_incomplete`**, never `broken`.
- **`summary.json` must be recomputable from the other files.** No claim about a file that is not in the return.
- **Write each repository's probe file as it finishes.** If you run out of time, return what finished and say how
  far the funnel got; 120 candidates fully screened beats 300 half-screened.
- **A low yield is the expected answer.** If 300 candidates yield 4, report 4.
- No analysis or recommendations. Return the files.
