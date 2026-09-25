# Assignment 09: re-test three repositories from assignment 08

**Phase:** P1 · P2 (see the README's phase tags)

Budget **2–4 hours**. Assignment 08 probed 20 repositories. Three of them did not get a fair verdict: one because
of a toolchain choice, two because the environment failed. Re-test exactly these three, at **the same eight
commits 08 used**, and give each a verdict.

## One rule changed since 08

**The 90-second build limit is dropped.** Captures run offline in batches, so a slow build costs only time.
The `slow` verdict no longer exists. Everything else in 08's verdict rules stands:

- **`capturable`** — 8/8 build **and** median static page count ≥ 8. Record the median build time; it no longer
  decides anything.
- **`spa`** — builds, median static page count ≤ 2. Name it; it is not "broken".
- **`broken`** — fewer than 8/8 build, **after** the toolchain rules below.
- **`environment_incomplete`** — your environment, not the repo, prevented a verdict.

## The three repositories

| repo | framework | 08 verdict | why it is being re-tested | commits (same eight as 08) |
|---|---|---|---|---|
| `swyxio/swyxdotio` | SvelteKit | broken | `engines` says `>=20`; 08 installed **Node 20.0.0**, and a dependency requires `^20.9.0`. That is a toolchain choice, not a broken repo | `bcf9bb3ccea1 101dffcf1917 fd15ddc93850 1c97ee5750b0 07172a9b6f62 a6a2345f2e1d b796d74a269e 6306a7c6a3cf` |
| `nemanjam/nemanjam.github.io` | Astro | environment_incomplete | yarn could not reach its registry ("trouble with your network connection") | `44f9f86e273f 6333be10bf83 5dc35d9eb87d 918e74a248fa 0b7c59fd2a7f 26189abd3f78 419952f55d3b 7fed9b43b849` |
| `querkmachine/beeps.website` | Eleventy | environment_incomplete | the build timed out on an outbound HTTPS request (`Socket.onTimeout`), wrote 0 files | `74dc73cd551a 09b2e0a2d27d 2eded9a40a6f e87b790eacd0 23276fd86320 6ed66e63aa98 094402c84645 477a1f74a9db` |

## Toolchain rules

- **A range means the newest release that satisfies it at the commit's date**, not the lowest. `>=20` on a
  2026 commit is the newest Node 20.x or 22.x LTS, **never** 20.0.0. Record the rung (`declared` →
  `lockfile-version` → `latest-at-commit-date`) as in 08.
- Use the package manager the lockfile names, pinned via corepack when `packageManager` is set.
- **swyxdotio first: read `svelte.config.js` at each commit and quote the adapter line.** If it is anything other
  than `@sveltejs/adapter-static` (or a prerender-everything config you quote), the verdict is `spa`/screen
  rejection, not a build result: record it and stop on that repo.

## Network failures (nemanjam, beeps)

These two failed on the network, which says nothing about the repos.

1. Before building, confirm the registry answers: `curl -sI https://registry.yarnpkg.com/` and
   `curl -sI https://registry.npmjs.org/`. Record the status lines.
2. Retry a failed install **up to three times**, with `--network-timeout 600000` for yarn.
3. **beeps.website fetches something over HTTPS during the build.** Find out what: quote the file and line
   (search the Eleventy config and `_data/` for `fetch`, `https://`, `EleventyFetch`). Then:
   - If the fetch target answers now, build normally.
   - If it is dead or unreachable, record the URL and the error. That repo is **`broken` for our purposes**
     (a build that needs a live third-party service cannot be replayed), and say so in `failure_stage:
     "external_fetch"`. Do not stub the fetch.

## Counting pages

As in 08 and assignment 07: Astro `.html` under `dist/` excluding `_astro/`; Eleventy `.html` under the configured
output dir (quote the config line naming it); SvelteKit static `.html` under `build/`. Count files on disk after the
build, never from a log.

## Output

```
output/
  environment.json                 Node versions available, package managers, registry curl results
  probes/<owner>__<repo>.json      same schema as 08's probe files, plus "node_range" (the declared range)
                                   and, for beeps, "external_fetch": {"file","line","url","result"}
  summary.json                     one row per repo: verdict, build_ok (n/8), median_static_page_count,
                                   median_build_seconds, and a one-line reason
```

## Rules

- **Never report a build you did not run**, or a page count you did not read from files on disk.
- **Verbatim error excerpts**, five real lines.
- **Environment failures are `environment_incomplete`**, never `broken`.
- **A low yield is fine.** If none of the three is capturable, report that.
- Write each repo's probe file as it finishes. No analysis or recommendations. Return the files.
