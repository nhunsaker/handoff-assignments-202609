# Research task: find 100 front-end repositories that can be built repeatedly across their own history

**Phase:** P2 (see the README's phase tags)

You are screening public GitHub repositories. Work entirely from the public web and from
`git` and `npm`/`pnpm` on your own machine. Nothing will be uploaded to you and you need no
files from me. Budget roughly 5 to 7 hours.

The goal is to find repositories whose **old commits still build today**. That is much rarer
than it sounds, and it is the only property that matters here. A repository with 40,000 stars
that cannot install its own dependencies from a year ago is worthless for this; an unknown
repository with a clean lockfile is valuable.

Work in **two stages**. Stage 1 is cheap and covers all 100. Stage 2 is expensive and covers
only what survives Stage 1. Do not attempt Stage 2 on all 100 — you will run out of time.

---

## Stage 0 — Build the candidate list (100 repos, stratified)

Use GitHub code and repository search. Fill these five buckets. If a bucket cannot be filled,
say so in the coverage note and move on rather than padding it with poor fits.

| bucket | target | what qualifies |
|---|---|---|
| A · Next.js + Tailwind | 35 | a real site or app, using both |
| B · Vite or CRA + React + Tailwind | 20 | a real site or app |
| C · Astro + Tailwind | 15 | a real site |
| D · Bootstrap | 20 | a site *using* Bootstrap, any build tool |
| E · plain CSS or SCSS, no utility framework | 10 | a real site |

Useful search syntax — vary it, these are starting points, not the whole search:

```
path:package.json tailwindcss next language:JavaScript pushed:>2025-01-01
path:package.json tailwindcss vite stars:>50
path:package.json bootstrap "scripts" pushed:>2025-06-01
path:astro.config.mjs tailwind
filename:tailwind.config.js path:/ stars:10..2000
```

### Exclusions — apply these before anything else, they are not negotiable

Reject a repository outright, and log it as rejected with the reason, if:

1. **It is owned by the organisation that publishes the framework it uses.** `tailwindlabs/*`
   using Tailwind, `vercel/next.js`, `withastro/*`, `twbs/*`. These are the framework
   documenting itself, not somebody building with it. This is the single most common way a
   scan like this goes wrong.
2. **It is documentation for a developer tool.** Docs sites for libraries, CLIs, APIs or
   frameworks. I want sites that people visit, not references that developers read.
3. **It is a starter, boilerplate, template, or "awesome" list.** No real change history.
4. **It is a monorepo where the site is one package among many.** Too fragile to build in
   isolation.
5. **It has no committed lockfile** (`package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`).
   No lockfile means old commits resolve today's dependency versions, which defeats the
   entire purpose.
6. **Fewer than 60 commits touching files that affect rendered pages** — see the definition
   in Stage 1.

---

## Stage 1 — Cheap metadata screen (all 100, no installing)

For each candidate, clone with `git clone --filter=blob:none` and read metadata only.
**Do not run `npm install` in this stage.** Record:

```json
{
  "repo": "owner/name",
  "url": "",
  "bucket": "A",
  "stars": 0,
  "lockfile": "package-lock.json | pnpm-lock.yaml | yarn.lock | none",
  "package_manager_pinned": "the packageManager field in package.json, or null",
  "node_version_pinned": "from .nvmrc, engines, or CI config; or null",
  "css_framework": "tailwind | bootstrap | none | other",
  "framework": "next | astro | vite-react | eleventy | other",
  "page_count_at_head": 0,
  "total_commits": 0,
  "page_touching_commits": 0,
  "densest_6_month_window": "YYYY-MM to YYYY-MM",
  "page_touching_commits_in_that_window": 0,
  "passes_stage_1": true,
  "rejection_reason": "null, or one of: framework-owned, tool-docs, template, monorepo, no-lockfile, too-few-page-commits, other (explain)"
}
```

**`page_touching_commits`** means commits that modify at least one file matching any of:
`*.html`, `*.astro`, `*.vue`, `*.svelte`, `*.jsx`, `*.tsx`, `*.css`, `*.scss`,
`tailwind.config.*`, or files under a `pages/`, `app/`, `src/pages/`, `content/` or
`_posts/` directory. Count with `git log --oneline -- <paths>`.

**`densest_6_month_window`** is the six-month span of this repository's history containing the
most page-touching commits. Find it by bucketing commit dates by month and sliding a
six-month window. This matters more than the total, because a corpus is built from a
contiguous stretch of history, not scattered across a decade.

**`page_count_at_head`** is your best estimate of how many distinct routes or pages the site
has, from counting files under the routes directory. An estimate is fine; say how you counted.

A repository passes Stage 1 if it clears every exclusion, has a lockfile, and has **at least
40 page-touching commits inside its densest six-month window**.

---

## Stage 2 — Deep build probe (only repos that passed Stage 1)

Expect roughly 25 to 40 repositories to reach this stage. If more than 45 pass, take the 45
with the highest `page_touching_commits_in_that_window` and note that you capped it.

For each, pick **six commits evenly spaced across the densest six-month window** — the oldest,
the newest, and four between. For each of the six, in a clean worktree:

1. `git checkout <sha>` then `git reset --hard` and remove ignored build caches.
2. Install using whatever the lockfile implies: `npm ci` for `package-lock.json`,
   `pnpm install --frozen-lockfile --ignore-workspace` for `pnpm-lock.yaml`,
   `yarn install --frozen-lockfile` for `yarn.lock`.
3. Run the build script from `package.json`.
4. **Time both steps.** Kill anything exceeding 300 seconds and record it as a timeout.

Record:

```json
{
  "repo": "owner/name",
  "window": "YYYY-MM to YYYY-MM",
  "commits_probed": ["sha1", "..."],
  "install_ok_count": 0,
  "build_ok_count": 0,
  "median_install_seconds": 0,
  "median_build_seconds": 0,
  "slowest_build_seconds": 0,
  "oldest_commit_builds": true,
  "failures": [
    {"sha": "", "stage": "install | build | timeout", "error_excerpt": "the last 5 lines of output, verbatim"}
  ],
  "verdict": "usable | slow | broken",
  "verdict_reason": ""
}
```

Verdict rules, apply them literally:

- **`usable`** — 6 of 6 install **and** 6 of 6 build, and `median_build_seconds` is **under
  60**. Both conditions. A repo that builds perfectly in 300 seconds is not usable, because
  sixty commits at that speed is a five-hour job.
- **`slow`** — builds 6 of 6 but median build is 60 seconds or more.
- **`broken`** — anything less than 6 of 6 on either install or build.

**`oldest_commit_builds` is the field I care about most.** A repository that builds at HEAD
and fails at the oldest probe is the exact failure mode this whole exercise exists to detect,
and it is invisible to any screen that only checks recent commits.

---

## Output

Four files:

- `stage1.json` — all 100 Stage 1 records, including every rejection.
- `stage2.json` — all Stage 2 records.
- `summary.json` — the funnel as plain counts: candidates found, rejected at each exclusion
  (broken out by reason), passed Stage 1, probed, and the counts of `usable` / `slow` /
  `broken`. Plus the same counts **per bucket A through E**, because I need to know whether
  reproducibility differs by stack — that is a finding in its own right.
- `searches.json` — every GitHub search query you ran, with result counts, including queries
  that returned nothing.

## Rules

- **Never report a build you did not run.** Every number in Stage 2 must come from a command
  that actually executed. If your environment cannot install something for an environmental
  reason — no network, out of disk, a missing system library — record that as an environment
  failure in `failures` with the error text, and do **not** score it as `broken`. Those are
  different things and conflating them would mislead me.
- **Verbatim error excerpts.** Five real lines of output, not your summary of them. The
  specific error text is how I tell a toolchain problem from a lockfile problem.
- **A low yield is the expected result and a fine answer.** A previous scan of 50 repositories
  found 5 usable. If you find 8 out of 100, report 8. Do not relax the verdict rules to
  produce a longer list — a padded list costs me more than an empty one, because I will spend
  days on a repository you scored generously.
- Do not add analysis, recommendations, or commentary. Return the four JSON files.
