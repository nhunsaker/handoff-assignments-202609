# Assignment 04: full build manifests for five repositories

**Phase:** P2 (see the README's phase tags)

Budget **12 hours**. This is slow, mechanical work and that is the point — it is the kind of
thing worth doing once, carefully, so nobody has to do it again.

Assignments 01 and 02 answered *"does this repository build at six sampled commits?"* This one
answers the follow-up for the survivors: **which commits, exactly, build — every one of them,
under what toolchain, in how long, producing how many pages.** The output is a manifest that
lets someone walk a repository's history commit-by-commit with no surprises.

You may clone repositories. Nothing will be uploaded to you.

---

## Phase 0 — Environment (30 min). STOP if it fails.

Confirm, and record in `environment.json`:

1. You can **switch Node versions** (`fnm`, `nvm`, `n`, or `volta`).
2. You can **pin package-manager versions** (`corepack enable` then `corepack prepare pnpm@X --activate`; `npm i -g npm@X` into a prefix you own).
3. The npm registry is reachable (`npm view pnpm versions` returns a list).
4. **Disk:** at least 20 GB free. Five repositories × many commits × `node_modules` adds up. Reuse one worktree per repository and clean it between commits; do not keep every checkout.

If you cannot switch Node versions, stop and say so. A manifest built on one fixed Node is the
mistake Assignment 02 exists to correct.

**Guard against the failure Assignment 02 hit:** the environment lost `pnpm` and `yarn` to a
reboot mid-run. After any interruption, re-verify Phase 0 before continuing and re-probe any
commit tested while a tool was missing.

---

## The five repositories

| # | repository | stack | note |
|---|---|---|---|
| 1 | `mrsibe/KnowNote` | Vite + React + Tailwind | 85 pages; window 2025-12 → 2026-05 had 97 page-touching commits |
| 2 | `vercel/commerce` | Next.js + Tailwind | passed a shallow probe once; **never probed under the six-commit bar** |
| 3 | `leerob/leerob.io` | Next.js + Tailwind | same — shallow probe only |
| 4 | `midudev/jsconf.es` | Astro + Tailwind | built 6/6 under an *inferred* toolchain; window 2024-12 → 2025-05 had ~280 page-touching commits |
| 5 | `11ty/eleventy-base-blog` | no framework | 13 pages, 4-second builds; a control |

Do them **in this order**. If time runs short, a complete manifest for four is worth more than
a partial one for five. **Repositories 2 and 3 are the ones I care about most** — they are the
only two Next.js candidates that have ever passed anything, and twenty other Next.js
repositories have produced nothing.

---

## Phase 1 — Window selection, corrected (per repository, ~15 min)

Find the densest six-month window of **page-touching commits**, exactly as in Assignment 01,
**with one correction that Assignment 02 exposed:**

> **The window must satisfy: `package.json` exists at every commit in it.**

Assignment 01 counted `*.html` and `*.css` commits from before some repositories had a build
system at all, and the "densest window" landed on history with nothing to build. Slide the
window past any span where `package.json` is absent.

Page-touching means a commit modifying at least one of: `*.html`, `*.astro`, `*.vue`,
`*.svelte`, `*.jsx`, `*.tsx`, `*.css`, `*.scss`, `tailwind.config.*`, or anything under
`pages/`, `app/`, `src/pages/`, `content/`, `_posts/`.

Record the window and the full list of page-touching commit SHAs in it. **You will probe every
one of them**, not a sample. If a repository has more than 150 in its window, take the 150 most
recent and say so.

---

## Phase 2 — Probe every commit (the bulk of the time)

For each commit in the window, in a clean worktree:

1. `git checkout <sha>`, `git reset --hard`, remove ignored build caches and `node_modules`.
2. **Resolve the toolchain** with this ladder and **record which rung you used**:
   - **Node:** `.nvmrc` / `.node-version` / `engines.node` at that commit → `declared`; else latest LTS on or before the commit date → `inferred_by_date`. LTS by start date: v12 2019-10 · v14 2020-10 · v16 2021-10 · v18 2022-10 · v20 2023-10 · v22 2024-10 · v24 2025-10. A range like `^20 || ^22` means the **lowest** satisfying version.
   - **Package manager:** `packageManager` in `package.json` via corepack → `declared`; else the lockfile's own declared format version → `lockfile_version` (`package-lock` `lockfileVersion` 1 → npm 6, 2 → npm 7-8, 3 → npm 9+; `pnpm-lock` `lockfileVersion` 5.3 → pnpm 6, 5.4 → pnpm 7, 6.0 → pnpm 8, 9.0 → pnpm 9-10; `yarn.lock` with `__metadata:` → berry, without → yarn 1); within that major, the latest release on or before the commit date; else latest-at-date → `inferred_by_date`.
3. Install per the lockfile. Time it. Kill at 300 s.
4. Run the build script. Time it. Kill at 300 s.
5. **If the build succeeded, count the routes it produced.** Count files in the build output directory that correspond to pages — `.html` files under `dist/`, `out/`, `build/`, `_site/`, or `.next/server/app/**/page.js` for Next.js. Record the count and *how you counted*, because this differs per framework.
6. Record the diff stat: how many files changed, and which of the page-touching patterns they matched.

Per-commit record:

```json
{
  "sha": "", "date": "YYYY-MM-DD", "subject": "first line of the commit message",
  "files_changed": 0, "page_files_changed": ["src/pages/index.astro"],
  "node_used": "v20.19.5", "node_rung": "declared | inferred_by_date",
  "pm_used": "pnpm@9.15.0", "pm_rung": "declared | lockfile_version | inferred_by_date",
  "install_ok": true, "install_seconds": 0,
  "build_ok": true, "build_seconds": 0,
  "route_count": 0, "route_count_method": "counted .html under dist/",
  "failure_stage": "install | build | timeout | environment | null",
  "error_excerpt": "last 5 lines verbatim, or null"
}
```

**Environment failures are not build failures.** A sandbox permission error, a missing system
library, a registry outage — `environment`, never `build`. Assignment 02 got this right and it
is the reason its numbers were usable.

---

## Phase 3 — Per-repository manifest

Write `output/<owner>__<repo>/manifest.json`:

```json
{
  "repo": "", "stack": "", "window": "YYYY-MM to YYYY-MM",
  "commits_in_window": 0, "commits_probed": 0, "capped": false,
  "commits": [ ...per-commit records... ],
  "summary": {
    "install_ok": 0, "build_ok": 0, "environment": 0,
    "build_ok_rate": 0.0,
    "median_build_seconds": 0, "p90_build_seconds": 0,
    "all_rungs_declared_count": 0,
    "route_count_min": 0, "route_count_median": 0, "route_count_max": 0,
    "buildable_commits_per_month": [{"month": "2026-01", "count": 0}],
    "longest_run_of_consecutive_buildable_commits": 0,
    "verdict": "usable | usable_inferred | slow | broken | environment_incomplete"
  }
}
```

Verdict rules, as in Assignment 02, applied to the **whole window** rather than six samples:

- **`usable`** — build_ok_rate ≥ 0.90, median build < 60 s, every rung `declared`.
- **`usable_inferred`** — same, but at least one commit needed an inferred version.
- **`slow`** — build_ok_rate ≥ 0.90 but median build ≥ 60 s.
- **`broken`** — build_ok_rate < 0.90 under a correctly resolved toolchain.
- **`environment_incomplete`** — your environment prevented a clean verdict. Say why.

**`longest_run_of_consecutive_buildable_commits`** is a field I care about specifically. A
repository that builds 90% of commits scattered across the window is different from one that
builds 90% in one unbroken stretch. Compute it in commit order.

---

## Phase 4 — Cross-repository summary (30 min)

`output/summary.json`: one row per repository with the summary block above, plus:

- **`expected_page_commit_pairs`** = `build_ok × route_count_median` — the number of
  (commit, page) pairs the repository could yield.
- Which of the five is the strongest by that number, and which Next.js repository (2 or 3) is
  stronger, or whether both are broken.
- A `toolchain_log.json` as in Assignment 02: every distinct (Node, package manager) pair you
  activated, and any you could not obtain.

---

## Phase 5 — Deliver the probe harness (30 min)

You have now built this probe twice. **Commit the harness itself** to `output/harness/` —
whatever language it is in — with a short `README.md` stating how to run it against any
repository and any window. Strip anything specific to this environment. The ladder in Phase 2
should be a function someone can read.

This is the one part of the assignment where I want code, not data.

---

## Rules

- **Never report a build you did not run.** Every number comes from a command that executed.
- **Verbatim error excerpts**, five real lines. The text is how a toolchain problem is told
  apart from a genuine one.
- **Reuse one worktree per repository.** Do not accumulate checkouts; Phase 0's disk check is
  there because this is the assignment most likely to fill a disk.
- **Report interruptions.** A reboot, a vanished tool, a deleted directory: say so, re-verify
  Phase 0, re-probe what was affected. Do not let numbers from a broken environment stand.
- **A repository that is broken across its whole window is a complete and valuable answer.**
  It closes a question. Do not soften it.
- **Write each manifest as soon as its repository finishes** — not all five at the end. If the
  run dies at hour nine, four manifests on disk are worth far more than none.
- No analysis or recommendations. Return the files.
