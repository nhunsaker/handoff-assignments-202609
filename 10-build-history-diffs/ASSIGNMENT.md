# Assignment 10: build every commit of three sites and record how each commit changed the built pages

**Phase:** P1 · P2 (see the README's phase tags)

Budget **14–20 hours**, most of it machine time. Assignment 08 found three sites whose commits build reliably and
emit real static pages. This assignment builds **every commit** in each site's window and records, commit by
commit, which built pages changed and how their HTML structure changed. Nothing is sampled: the point is the
complete history.

The three sites and their windows (the same windows 08 used, stated here as exact dates):

| repo | framework | window (`--since`, `--until`) | first-parent commits | 08 median build |
|---|---|---|---|---|
| `tempertemper/www.tempertemper.net` | Eleventy | `2025-07-01`, `2026-01-01` | 100 | 10 s |
| `efcl/efcl.github.io` | Jekyll (Ruby) | `2025-04-01`, `2025-10-01` | 74 | 231 s |
| `alexcarpenter/alexcarpenter.me` | Astro | `2025-04-01`, `2025-10-01` | 281 | 139 s |

**Do them in that order.** tempertemper takes under an hour; efcl about five; alexcarpenter about eleven. If you
run out of time, a complete tempertemper plus a partial alexcarpenter is worth far more than three partials.
Write every file as it finishes so that partial work comes back.

You may clone repositories and run builds. Nothing will be uploaded to you.

---

## Phase 0 — Environment (20 min)

Node via a version manager, corepack, npm/pnpm/yarn, git, **Ruby + Bundler** (efcl pins a version in
`.ruby-version`; use it), ≥ 40 GB free. Record in `environment.json`, including the registry checks
`curl -sI https://registry.npmjs.org/` and `curl -sI https://rubygems.org/` (status lines verbatim).

---

## Phase 1 — The commit list

For each repo, on the default branch:

```
git log --first-parent --reverse --since=<start> --until=<end> --format='%H %aI %s'
```

**First-parent only**, oldest first. Record for each commit: `sha`, `author_date`, `subject` (first line,
verbatim), `files_changed` (from `git show --stat`), and `page_touching` (true if it modifies `*.html`,
`*.astro`, `*.vue`, `*.svelte`, `*.jsx`, `*.tsx`, `*.md`, `*.css`, `*.scss`, `tailwind.config.*`, or anything
under `pages/`, `app/`, `src/pages/`, `content/`, `_posts/`, `_site/` sources). Output `commits/<owner>__<repo>.json`.

---

## Phase 2 — Build every commit and hash every page

Per commit, in order:

1. **Clean worktree** at that commit (`git worktree add`, then remove it after; never build in a dirty tree,
   never reuse a previous commit's output directory).
2. **Toolchain**, recorded per commit with its rung:
   - **Node:** a range means the **newest release satisfying it at the commit's date**, never the lowest
     (`>=20` on a 2025 commit is the newest 20.x/22.x LTS at that date, not 20.0.0). Rungs: `declared`
     (engines / `.nvmrc` / `.node-version`) → `lockfile-version` → `latest-lts-at-commit-date`.
   - **Package manager:** what the lockfile names; `packageManager` pinned through corepack when present.
   - **Ruby:** `.ruby-version`, then `Gemfile.lock`'s `BUNDLED WITH`.
   - **Install caching is allowed and encouraged:** key an install cache on the sha256 of the lockfile
     (`package-lock.json` / `pnpm-lock.yaml` / `yarn.lock` / `Gemfile.lock`) and reuse `node_modules` or the
     bundle when the hash matches. Record `install_cache_hit` per commit. **Build output is never cached.**
3. **Build** with the repo's own build script (`npm run build`, `bundle exec jekyll build`, ...). Record the
   command verbatim and wall-clock seconds. Timeout: 15 minutes per build.
4. **Hash every page.** Walk the output directory (Eleventy: the dir named in its config — quote the line;
   Jekyll: `_site/`; Astro: `dist/` excluding `_astro/`). For every `*.html` file record its path relative to
   the output root and the sha256 of its bytes. Write `manifests/<owner>__<repo>/<sha>.json`:

   ```json
   { "sha": "", "output_root": "", "page_count": 0, "pages": { "index.html": "sha256…", "posts/foo/index.html": "…" } }
   ```

   Also record the sha256 of every non-HTML file under the output root in a separate `assets` map (CSS, JS,
   images), so a commit that changed only a stylesheet is visible.

Per commit, a probe row in `probes/<owner>__<repo>.json` with the 08 schema (`node_used`, `node_rung`,
`pm_used`, `install_ok`, `build_ok`, `build_seconds`, `static_page_count`, `count_method`, `failure_stage`,
`error_excerpt`) plus `install_cache_hit` and `build_command`.

**A failed build gets no manifest.** Do not fill in a manifest from a neighbouring commit.

---

## Phase 3 — What each commit changed (from the manifests; cheap)

For each **consecutive pair of successfully built commits** (when a commit in between failed, pair across it and
record the skipped shas), compare the two manifests:

```json
{
  "from": "sha", "to": "sha", "skipped": [],
  "pages_added": ["path"], "pages_removed": ["path"], "pages_modified": ["path"],
  "pages_unchanged": 0,
  "assets_added": 0, "assets_removed": 0, "assets_modified": ["path"],
  "source_files_changed": ["src/…"]
}
```

`source_files_changed` is `git diff --name-only from to`. Output `pairs/<owner>__<repo>.json`.

---

## Phase 4 — How each modified page's structure changed

For every page in `pages_modified`, parse **both** versions with a real HTML parser (parse5, cheerio, jsdom,
Python `html5lib` or `lxml`; name it in `environment.json`) and compute, on the `<body>` subtree:

1. **Element counts** before and after.
2. **Sibling-group changes.** For every element whose children include two or more children of the same tag, treat
   those same-tag children as a group. Match children across versions by `(tag, id attribute if any, sha256 of
   normalized text content)` where normalized means whitespace collapsed, trimmed. A group whose count changed, or
   whose matched members changed order, is an event:

   ```json
   {
     "page": "index.html",
     "container": "body > main > ul",          // CSS path of the parent, nth-of-type on every step
     "child_tag": "li",
     "before_count": 12, "after_count": 13,
     "kind": "insert | remove | reorder | mixed",
     "positions": [0],                          // 0-based indices of inserted/removed members in the AFTER (insert) or BEFORE (remove) list
     "matched": 12, "unmatched_before": 0, "unmatched_after": 1
   }
   ```

3. **Text-only changes:** elements matched by position whose tag and attributes are identical and only text
   differs — a count.
4. **Attribute-only changes:** same, attributes differ, text identical — a count, plus the set of attribute names
   that changed.

Output `structure/<owner>__<repo>.json`: one row per (pair, page) with the four results. Record the parser and
the exact matching rule you implemented; if you deviate from the rule above, say where and why.

**Snapshots.** For each sibling-group event of kind `insert` or `remove`, save the before and after HTML of that
page under `snapshots/<owner>__<repo>/<from>__<to>/<page path>.before.html` and `.after.html`, **until the
snapshot directory reaches 120 MB across all three repos**; after that record only hashes and note the cutoff
in `summary.json`. Files larger than 600 KB are never snapshotted (hashes only).

---

## Phase 5 — Summary

`summary.json`, per repo: commits in window, built, failed (by `failure_stage`), install cache hit rate, median
build seconds, median page count, pairs analysed, median `pages_modified` per pair, distribution of
`pages_modified` (0 / 1 / 2–5 / 6–20 / 21+), total sibling-group events by kind, the **20 containers with the
most events** (path, page, count), snapshot count and total MB, and how much of the window you completed.

---

## Output

```
output/
  environment.json
  commits/<owner>__<repo>.json
  probes/<owner>__<repo>.json
  manifests/<owner>__<repo>/<sha>.json
  pairs/<owner>__<repo>.json
  structure/<owner>__<repo>.json
  snapshots/<owner>__<repo>/<from>__<to>/<page>.before.html | .after.html
  summary.json
```

Total output must stay under **200 MB**. Manifests and structure files are small; the snapshot cap above is
what keeps the rest in bounds.

## Rules

- **Never report a build you did not run**, a hash you did not compute from a file on disk, or an event you did
  not derive from two parsed files. A count from a build log is not a count of build output.
- **Verbatim error excerpts**, five real lines, for every failed build.
- **Environment failures are `environment_incomplete`**, never `broken`.
- **A commit that fails to build is a real result.** Do not retry with a different toolchain to make it pass
  unless the first choice violated the toolchain rules above; if you do retry, record both attempts.
- **Write each repo's files as commits finish.** A partial tempertemper with 60 manifests is useful; a promise of
  a complete one is not.
- No analysis or recommendations. Return the files.
