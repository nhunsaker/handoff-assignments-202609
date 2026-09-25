# Assignment 08: find sites that can actually be captured, not merely built

**Phase:** P1 · P2 (see the README's phase tags)

Budget **10–14 hours**. Four previous scans found repositories that build and then turned out to
be useless for a different reason each time. This one screens for the properties that actually
matter, in the order that kills candidates fastest.

## Why the earlier scans failed

Read this before starting; every rule below exists because something slipped through.

| scan | what it screened for | what slipped through |
|---|---|---|
| n=50 | stars, activity, lockfile | repos whose old commits will not install |
| n=100 | install + build at 6 commits | 3 of 4 "usable" were 1–3 page toy apps |
| toolchain re-probe | build under a date-matched toolchain | windows landing on pre-JS history |
| build manifests | every commit in the densest window | densest window was **2020** for two repos; and the strongest candidate by build rate turned out to be `output: 'server'` — it builds in 3 seconds and emits **one** HTML file, because its pages render at request time |

**Buildability is not capturability.** A repository can build 146 of 150 commits and still be
worthless if the build emits no static pages. That is the single most important filter here and
no previous scan had it.

You may clone repositories and run builds. Nothing will be uploaded to you.

---

## Phase 0 — Environment (20 min)

Node 20/22, npm, pnpm, yarn, git, ≥30 GB free. Confirm you can switch Node versions and pin
package-manager versions (corepack). Record in `environment.json`. If you cannot switch Node,
say so and continue — most candidates will be recent.

---

## Phase 1 — Candidate list (150 repos)

GitHub search. Target **150** candidates so the funnel has room; earlier scans lost 90% by
Stage 2. Stratify:

| bucket | target | note |
|---|---|---|
| A · Astro + Tailwind, **static output** | 40 | exclude `output: 'server'` — see Phase 2 |
| B · Next.js, **static export** | 30 | needs `output: 'export'` or a fully prerendered app |
| C · Eleventy / Hugo / Jekyll | 35 | static by construction; historically the best survivors |
| D · Vite/React SPA with a static build | 25 | |
| E · Nuxt / SvelteKit **static preset** | 20 | |

Reject at intake, logging the reason: framework-owned repos (`tailwindlabs/*`, `withastro/*`,
`twbs/*`), documentation for a developer tool, starters/boilerplate/templates, monorepos where
the site is one package, and **no committed lockfile**.

---

## Phase 2 — The capturability screen (cheap, no builds yet)

This is the new filter and it runs **before** any install. For each candidate, read the config
at HEAD:

```json
{
  "repo": "", "framework": "astro|next|eleventy|hugo|jekyll|vite|nuxt|sveltekit",
  "output_mode": "static | server | hybrid | unknown",
  "evidence": "verbatim line from astro.config/next.config/nuxt.config, or 'no output setting (defaults to static)'",
  "adapter": "vercel | netlify | node | none",
  "source_page_count": 0,
  "passes_capturability_screen": true,
  "rejection_reason": null
}
```

**Reject** any repo whose config sets `output: 'server'`, `output: 'hybrid'`, or ships a runtime
adapter (`@astrojs/vercel`, `@astrojs/node`, `next` without `output: 'export'`, `nitro` preset
`node`). Reject any with **fewer than 8 source pages**.

Quote the config line. "It looked static" is not evidence.

---

## Phase 3 — Window selection, with a recency floor

For survivors, find the six-month window with the most page-touching commits, subject to **all**
of:

1. **`package.json` exists at every commit in it.**
2. **The window ends no earlier than 24 months before today.** Earlier scans chose 2020 windows
   because heaviest page churn is early repo life. If no window in the last 24 months has ≥25
   page-touching commits, **reject the repo** and say so.
3. At least **25** page-touching commits in the window.

Page-touching means a commit modifying `*.html`, `*.astro`, `*.vue`, `*.svelte`, `*.jsx`,
`*.tsx`, `*.css`, `*.scss`, `tailwind.config.*`, or anything under `pages/`, `app/`,
`src/pages/`, `content/`, `_posts/`.

---

## Phase 4 — Build and count STATIC PAGES (the real test)

Probe **eight** commits evenly spaced across the window. Per commit: clean worktree, resolve the
toolchain (declared → lockfile-version → latest-at-commit-date, recording which rung), install,
build, then **count static HTML pages in the build output**.

Counting rules by framework, and you must record which you used:

| framework | count |
|---|---|
| Astro | `.html` under `dist/`, excluding `_astro/` |
| Next static export | `.html` under `out/` |
| Eleventy | `.html` under `_site/` |
| Hugo | `.html` under `public/` |
| Jekyll | `.html` under `_site/` |
| Vite/SPA | `.html` under `dist/` — **if this is 1, the repo is an SPA and fails** |

```json
{
  "sha": "", "date": "", "node_used": "", "node_rung": "", "pm_used": "", "pm_rung": "",
  "install_ok": true, "build_ok": true, "build_seconds": 0,
  "static_page_count": 0, "count_method": "",
  "failure_stage": null, "error_excerpt": null
}
```

### Verdict

- **`capturable`** — 8/8 build, **median static page count ≥ 8**, median build < 90 s.
- **`spa`** — builds, but median static page count ≤ 2. **This is the `jsconf.es` failure and
  it must be called out by name, not folded into "broken."**
- **`slow`** — 8/8 build, median ≥ 90 s.
- **`broken`** — fewer than 8/8.
- **`environment_incomplete`** — your environment prevented a verdict.

---

## Phase 5 — Output

```
output/
  environment.json
  capturability_screen.json     Phase 2, all 150, including rejections
  windows.json                  Phase 3, with rejections and their reason
  probes/<owner>__<repo>.json   Phase 4, per repo
  summary.json                  the funnel: 150 → screened → windowed → probed → by verdict,
                                broken out PER BUCKET, plus the capturable list ranked by
                                (median static page count × page-touching commits in window)
  searches.json                 every query, with result counts and zero-result queries
```

## Rules

- **Never report a build you did not run**, or a page count you did not derive from files on
  disk. A count from source files or from a build log is not a count of build output.
- **Verbatim error excerpts**, five real lines.
- **`spa` is a distinct verdict.** A repo that builds perfectly and emits one page is not
  "broken" and must not be reported as such — it is the most important thing this scan exists to
  detect.
- **A low yield is the expected answer.** Four scans have produced one usable site between them.
  If 150 candidates yield 3, report 3. **Do not relax a verdict to lengthen the list.**
- **Environment failures are `environment`**, never `broken`.
- **Write each repo's probe file as it finishes.**
- No analysis or recommendations. Return the files.
