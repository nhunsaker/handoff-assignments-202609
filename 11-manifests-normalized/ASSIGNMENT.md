# Assignment 11: per-commit manifests for tempertemper, raw and normalized, plus insertion snapshots

Budget **2–4 hours**, mostly machine time. Assignment 10 did the hard part but two of its deliverables did not come
back: the per-commit **manifests** (`manifests/<owner>__<repo>/<sha>.json`) were never written, and the before/after
**HTML snapshots** were not returned (the summary says the 120 MB budget was used; on disk it is 124,592 bytes, two
pointers, zero HTML files). This assignment produces both, for **one** repository, with one addition.

**Repository:** `tempertemper/www.tempertemper.net`. **Commits:** exactly the 102 in
`10-build-history-diffs/output/commits/tempertemper__www.tempertemper.net.json`, in that order. Use the same
toolchain per commit that 10 recorded in its probe file; if a commit's recorded toolchain no longer works, say so.

## Why a second hash

Every built page contains a build timestamp in a cache-busting query string:

```
<link rel="preload" href="/assets/css/non-critical.css?v=1790336771992" …
```

`?v=` is milliseconds since the epoch at build time. It changes on every build, so every page's raw bytes differ
between any two builds whether or not anything changed. That is why 10 reported a median of 526 of 547 pages
"modified" per commit. Record **both** a raw hash and a normalized hash so the two can be compared on the same builds.

## Per commit

1. Clean worktree, same install cache rule as 10 (key on the lockfile sha256; never cache build output).
2. Build. Record wall-clock seconds.
3. Write `manifests/<sha>.json`:

```json
{
  "sha": "", "output_root": "dist", "page_count": 0,
  "pages":  { "blog/index.html": { "raw": "sha256…", "normalized": "sha256…", "body": "sha256…" } },
  "assets": { "assets/css/non-critical.css": "sha256…" }
}
```

- **`raw`** — sha256 of the file bytes.
- **`normalized`** — sha256 after these replacements, **in this order, and no others**:
  1. every `?v=<digits>` inside an attribute value → `?v=0`;
  2. any other query-string parameter whose value is 10–13 digits → the same parameter with value `0` (record every
     parameter name you normalize this way, per page, in `normalized_params`);
  3. CRLF → LF.
- **`body`** — sha256 of the serialized `<body>` subtree only, parsed with `lxml.html` (the parser 10 used) and
  re-serialized with `lxml.html.tostring(body, method="html", encoding="unicode")`.

If you find another value that changes between two builds of the **same commit** (step 5), do not add a rule for
it. Record it; that is assignment 13's job.

## Snapshots — targeted, not budgeted

For every consecutive pair where `blog/index.html`, `blog/year/*.html` or `category/*.html` has a different
**`body`** hash, save both versions:
`snapshots/<from12>__<to12>/<page path with / as __>.before.html` and `.after.html`. No size cap for these pages.

## Step 5 — determinism control

Build **three** commits a second time in a fresh worktree with an empty build output directory (first, middle,
last of the 102): compare all three hashes for every page. Report per commit how many pages differ in `raw`,
`normalized` and `body` between the two builds of the same commit. **Expected:** `raw` differs on nearly every
page; `normalized` and `body` differ on none. Report what you actually get.

## Output

```
output/
  environment.json
  manifests/<sha>.json                     102 files (or as many as built; failures listed in summary)
  pairs.json                               per consecutive pair: pages_modified by raw, by normalized, by body
  snapshots/<from12>__<to12>/…before.html|after.html
  determinism.json                         step 5
  summary.json                             built/failed, median pages modified per pair under each hash,
                                           snapshot count and MB, anything unexpected
```

## Rules
- **Never report a hash you did not compute from a file on disk**, or a build you did not run.
- **Write each manifest as its commit finishes.** Partial work must come back.
- **`summary.json` must match the files.** Every number in it must be recomputable from the other files you return.
  Assignment 10's summary claimed files that were not in the return; that must not happen again.
- No analysis or recommendations. Return the files.
