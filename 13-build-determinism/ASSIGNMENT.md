# Assignment 13: what makes a static build non-deterministic, and which normalizations are safe

Budget **12–18 hours**. When the same commit of a static site is built twice, the output is often not byte-identical.
Assignment 10 found one cause the hard way: a build-time millisecond timestamp in a cache-busting query string
(`non-critical.css?v=1790336771992`) that made every page of one site differ on every build. There are many other
causes (build dates in footers, content hashes in asset filenames, random ids, unordered iteration, locale and
timezone, embedded git metadata, live network data).

This assignment catalogues **every** difference between repeated builds across twelve real sites, classifies each by
cause, and then **tests** normalization rules: a rule is only useful if it removes the noise **and** still lets real
content changes through. Both halves are measured, not argued.

You may clone repositories and run builds. Nothing will be uploaded to you.

## The twelve sites

All previously built by assignments 08–10. Use each site's window from those assignments.

| repo | framework | source of the window and toolchain |
|---|---|---|
| `tempertemper/www.tempertemper.net` | Eleventy | 10 |
| `efcl/efcl.github.io` | Jekyll | 10 |
| `alexcarpenter/alexcarpenter.me` | Astro | 10 |
| `querkmachine/beeps.website` | Eleventy | 09 |
| `nemanjam/nemanjam.github.io` | Astro | 09 |
| `cubxxw/blog` | Hugo | 08 |
| `yunyuyuan/nuxt3-blog` | Nuxt | 08 |
| `godruoyi/gblog` | Astro | 08 |
| `rimzzlabs/website` | Astro | 08 |
| `madrilene/lenesaile.com` | Eleventy | 08 |
| `hnpf/stabbed.wtf` | Vite | 08 |
| `elsbrock/hetzner-radar` | SvelteKit | 08 |

Per site, pick **three commits that built** in the earlier assignment (earliest, middle, latest successful in the
window). If a commit no longer builds, pick the nearest one that does and say so.

## Phase 1 — Repeated builds

Per commit, **four** builds, each in a fresh worktree with an empty output directory and the same toolchain:

| build | what varies |
|---|---|
| `b1` | baseline |
| `b2` | same as `b1`, a few minutes later |
| `b3` | `TZ=Pacific/Auckland` and `LANG=de_DE.UTF-8` (install the locale if needed; if you cannot, say so) |
| `b4` | a fresh install cache (delete `node_modules` / the bundle / Hugo's module cache first) |

Record for each build: command, seconds, output file count, and a manifest of every output file (HTML and
non-HTML) → sha256 of its bytes.

## Phase 2 — Every difference, located and classified

For each commit, compare `b2`, `b3` and `b4` against `b1`, file by file.

- **Files present in one build and not the other:** list them (content-hashed asset filenames show up here).
- **Files present in both with different bytes:** for **text** files (HTML, CSS, JS, JSON, XML, TXT), compute a
  character-level diff and extract every differing region with ±60 characters of context. Deduplicate regions that
  differ by the same pattern across files. For **binary** files, record only that they differ and their sizes.

Classify every distinct difference into exactly one cause:

| cause | recognise it by |
|---|---|
| `build_timestamp` | a date/time or epoch value equal (± 10 min) to the build time |
| `cache_buster_query` | a query parameter on an asset URL whose value changes per build |
| `content_hash_filename` | an asset filename (or reference to one) containing a hash that changes |
| `random_id` | an id/nonce/uuid-like token with no relation to content or time |
| `ordering` | the same items in a different order |
| `locale_timezone` | differs only between `b1` and `b3` |
| `dependency_resolution` | differs only between `b1` and `b4` |
| `git_metadata` | a commit hash, branch or git date embedded in output |
| `live_data` | content that comes from a network fetch at build time (quote the source line that fetches) |
| `other` | anything else — describe it and quote it |

Output `differences/<owner>__<repo>.json`: per distinct difference, the cause, the files it appears in (count +
five examples), one verbatim before/after region, and which build comparisons show it (`b2`, `b3`, `b4`).

## Phase 3 — Normalization rules

From the differences, write **the smallest set of normalization rules** (regular expressions or DOM operations,
applied to text files before hashing) that makes `b1` and `b2` identical for every HTML page at every commit. Write
them as data, not prose, in `rules.json`:

```json
[
  { "id": "R1", "cause": "cache_buster_query", "applies_to": "html",
    "kind": "regex", "pattern": "(\\?v=)\\d{10,13}", "replacement": "\\g<1>0",
    "sites_needing_it": ["tempertemper/www.tempertemper.net"] }
]
```

Prefer rules scoped to one site over one broad rule when a broad rule would also match content. Rules for `b3`
(locale/timezone) and `b4` (dependency) differences go in the same file, marked with the build they address.

## Phase 4 — Test the rules both ways (the part that matters)

A rule that deletes every number would make any two builds identical. That is useless. Measure both properties:

1. **Noise removal.** Apply the rules to every build of every commit. Report, per site and per build comparison
   (`b1`↔`b2`, `b1`↔`b3`, `b1`↔`b4`), how many HTML pages have identical hashes **before** and **after** normalization.
2. **Signal retention.** For each site, take the **real** differences between two consecutive commits that changed
   content (use one pair from the earlier assignment's window where a content file changed; list which source files
   changed). Build both commits (`b1` of each is enough), then report:
   - pages that differ **before** normalization;
   - pages that differ **after** normalization;
   - for every page that differed before and **not after**: the region(s) the rules removed, verbatim. **Any such page
     whose removed region is real content (a post title, a date the author wrote, body text) is a rule defect** —
     mark it `signal_lost: true` and name the rule that caused it.

Then, only if a rule has `signal_lost`, narrow it and re-run Phase 4 for that site. Record both versions.

## Output

```
output/
  environment.json                 toolchains, the locale actually used for b3, and anything you could not do
  builds/<owner>__<repo>/<sha12>/<b1|b2|b3|b4>.json     manifests (path → sha256, plus command and seconds)
  differences/<owner>__<repo>.json                       Phase 2
  rules.json                                             Phase 3 (final version)
  rules-history.json                                     every earlier version you narrowed, and why
  evaluation/<owner>__<repo>.json                        Phase 4, both halves
  summary.json                     per site: builds run, distinct differences by cause, pages identical b1↔b2
                                   before/after normalization, signal-retention result, any signal_lost
```

## Check-ins and review

This assignment follows the repository's **check-in, self-check and review protocol** (README, "Check-ins,
self-check and review"): push `output/` at every phase boundary and at least every 2 hours with an updated
`PROGRESS.md`; before the final commit, append the return manifest and re-derive every `summary.json` number from
the returned files; after the final commit, watch for `REVIEW.md` with `status: corrections_requested` and address
every numbered item in a new commit.

## Rules
- **Never report a difference you did not extract from two files on disk.** Quote regions verbatim.
- **A site whose builds are already byte-identical is a finding.** Report it; do not invent rules for it.
- **Do not normalize away `live_data`.** Record it with the fetching line. A rule that hides live data would make
  a site look reproducible when it is not.
- **Environment failures are recorded as such**, per build.
- **`summary.json` must be recomputable from the other files.** No claim about a file that is not in the return.
- **Write each site's files as it finishes.** Twelve sites × three commits × four builds is 144 builds; if you run
  out of time, complete sites are worth far more than partial ones. Do them in the table's order.
- No analysis or recommendations. Return the files.
