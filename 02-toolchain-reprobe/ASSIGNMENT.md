# Research task: re-probe 41 repositories with a date-matched toolchain

You are re-testing 41 GitHub repositories that a previous scan marked "broken". Budget 5 to 7
hours. Nothing will be uploaded to you; everything you need is below or on the public web.

## Why this is being re-run

The previous scan built every repository with **one fixed toolchain — Node 24.20.0, npm 10.9.4,
pnpm 10.34.5, yarn 1.22.22** — and ignored each repository's declared versions. It then probed
commits reaching back to 2013. Nineteen of its 41 failures were lockfile or package-manager
version errors, which tells you very little about the repository and a lot about the toolchain.

**Your job is to find out how many of these 41 are genuinely broken and how many were failed by
the probe.** A repository that builds cleanly under its own contemporary toolchain is a success,
not a failure.

## Step 0 — verify your environment, and stop if it is inadequate

Before probing anything, confirm you can do all three of these, and report what you found:

1. **Switch Node versions** — `fnm`, `nvm`, `n`, or `volta`. Install one if you can.
2. **Switch package-manager versions** — `corepack enable`, then `corepack prepare pnpm@8.15.6 --activate` style pinning; and for npm, `npm i -g npm@9` into a prefix you control.
3. **Reach the npm registry** — `npm view pnpm versions` returns a list.

If you cannot switch Node versions, **stop and say so**. A re-probe on a fixed Node is exactly
the run we already have and repeating it is worthless. That is a valid, useful answer.

Record the versions you can actually obtain. If the environment is non-persistent, re-verify
after any reboot and re-probe anything tested while a tool was missing — the previous run lost
`pnpm` and `yarn` to a reboot mid-task.

## Step 1 — resolve the toolchain per commit

For **each commit you check out**, resolve Node and the package manager independently, using
this ladder. **Record which rung you used** — this matters as much as the result.

### Node version

1. `.nvmrc`, `.node-version`, or `engines.node` **in the tree at that commit** → rung `declared`
2. Otherwise: **the latest Node LTS released on or before that commit's date** → rung `inferred_by_date`

Node LTS by date (use the latest whose start date precedes the commit):
`v12` 2019-10 · `v14` 2020-10 · `v16` 2021-10 · `v18` 2022-10 · `v20` 2023-10 · `v22` 2024-10 · `v24` 2025-10

A range like `^22 || ^24` means pick the **lowest** satisfying version — it is what the author most likely used.

### Package manager

1. `packageManager` field in `package.json` at that commit, via corepack → rung `declared`
2. Otherwise **read the lockfile's own declared format version** → rung `lockfile_version`:

| file | field | implies |
|---|---|---|
| `package-lock.json` | `"lockfileVersion": 1` | npm 6 |
| | `"lockfileVersion": 2` | npm 7 or 8 |
| | `"lockfileVersion": 3` | npm 9+ |
| `pnpm-lock.yaml` | `lockfileVersion: 5.3` | pnpm 6 |
| | `lockfileVersion: 5.4` | pnpm 7 |
| | `lockfileVersion: 6.0` | pnpm 8 |
| | `lockfileVersion: 9.0` | pnpm 9 or 10 |
| `yarn.lock` | has `__metadata:` block | yarn 2+ (berry) |
| | no `__metadata:` block | yarn 1 (classic) |

3. Within the implied major, pick **the latest release on or before the commit date** → still rung `lockfile_version`. If the lockfile has no version field at all, use latest-at-date and mark the rung `inferred_by_date`.

**This is an assumption and I want it labelled as one.** A build that only succeeds under an
inferred version is not equivalent to one that succeeds under a declared version, and I need to
be able to tell them apart afterwards.

## Step 2 — probe

For each repository, probe **the same six commits the previous scan used** where you can
determine them, otherwise six evenly spaced across the window given in the table. For each
commit, in a clean worktree: `git checkout <sha>`, `git reset --hard`, remove ignored caches,
activate the resolved Node and package manager, install per the lockfile, then run the build
script. Time both. Kill anything past 300 seconds and record it as a timeout.

## The 41 repositories

Columns: repo · bucket · lockfile · declared Node · declared packageManager · window · previous install/build out of 6.
A dash means the repository declares nothing and you must infer.

| repo | bkt | lockfile | node | packageManager | window | prev |
|---|---|---|---|---|---|---|
| alanagoyal/alanagoyal | A | package-lock.json | 24.x | — | 2024-09 to 2025-02 | 5/0 |
| aulianza/aulianza.id | A | yarn.lock | 20 | — | 2023-05 to 2023-10 | 1/0 |
| burhan-syed/troddit | A | yarn.lock | — | yarn@1.22.19+sha1.4ba7fc5c6e704fce2066ecbfb0b0d8976fe62447 | 2021-09 to 2022-02 | 0/0 |
| CaliCastle/cali.so | A | pnpm-lock.yaml | ^22.22.2 || ^24.15.0 || >=26.0.0 | pnpm@10.34.5 | 2026-04 to 2026-09 | 3/1 |
| exa-labs/company-researcher | A | package-lock.json | — | — | 2024-11 to 2025-04 | 6/1 |
| HelloGitHub-Team/geese | A | yarn.lock | 18 | — | 2022-07 to 2022-12 | 0/0 |
| hyperlink-academy/leaflet | A | package-lock.json | >=22.13 | — | 2026-04 to 2026-09 | 0/0 |
| jackblatch/OneStopShop | A | package-lock.json | — | — | 2023-04 to 2023-09 | 1/0 |
| mehrabmp/kara-shop | A | pnpm-lock.yaml | — | — | 2022-07 to 2022-12 | 0/0 |
| mldangelo/personal-site | A | package-lock.json | 26 | — | 2016-01 to 2016-06 | 0/0 |
| pheralb/slug | A | pnpm-lock.yaml | — | pnpm@8.15.6 | 2023-11 to 2024-04 | 0/0 |
| priyankarpal/projectshut | A | pnpm-lock.yaml | — | — | 2023-07 to 2023-12 | 0/0 |
| Ryczko/FormsLab | A | package-lock.json | — | — | 2022-03 to 2022-08 | 6/5 |
| samuelkraft/samuelkraft-next | A | yarn.lock | — | — | 2021-01 to 2021-06 | 0/0 |
| sanidhyy/duolingo-clone | A | pnpm-lock.yaml | lts/* | pnpm@11.11.0 | 2024-03 to 2024-08 | 6/2 |
| satnaing/satnaing.dev | A | package-lock.json | — | — | 2022-03 to 2022-08 | 6/4 |
| spencerwooo/onedrive-vercel-index | A | pnpm-lock.yaml | — | — | 2021-09 to 2022-02 | 0/0 |
| spliit-app/spliit | A | package-lock.json | >=24 | — | 2023-12 to 2024-05 | 1/0 |
| w3bdesign/nextjs-woocommerce | A | pnpm-lock.yaml | 24 | pnpm@12.3.4 | 2020-05 to 2020-10 | 5/0 |
| zenorocha/zenorocha.com | A | package-lock.json | — | — | 2013-01 to 2013-06 | 0/0 |
| devops329/jwt-pizza | B | package-lock.json | — | — | 2024-04 to 2024-09 | 6/5 |
| PasteBar/PasteBarApp | B | package-lock.json | — | — | 2024-04 to 2024-09 | 4/0 |
| santifer/cv-santiago | B | package-lock.json | 20 | — | 2026-01 to 2026-06 | 6/5 |
| achamorro-dev/eventoswiki | C | pnpm-lock.yaml | v24.16.0 | pnpm@11.23.0 | 2023-12 to 2024-05 | 0/0 |
| alexcarpenter_alexcarpenter.me | C | pnpm-lock.yaml | 24.x | pnpm@11.6.0 | 2023-07 to 2023-12 | 5/1 |
| aosasona/trulyao.dev | C | pnpm-lock.yaml | — | — | 2024-03 to 2024-08 | 2/2 |
| CanCLID/jyutping.org | C | package-lock.json | 22 | — | 2020-02 to 2020-07 | 6/0 |
| dreyfus92/astro-portfolio | C | pnpm-lock.yaml | — | — | 2022-11 to 2023-04 | 0/0 |
| jestsee_jestsee.com | C | pnpm-lock.yaml | 22.x | pnpm@9.15.9 | 2024-09 to 2025-02 | 0/0 |
| justjavac/esowiki | C | yarn.lock | — | — | 2022-11 to 2023-04 | 1/0 |
| midudev/jsconf.es | C | pnpm-lock.yaml | — | — | 2024-12 to 2025-05 | 5/5 |
| midudev/lolalolitaland.com | C | pnpm-lock.yaml | — | — | 2025-03 to 2025-06 | 4/4 |
| surge-synthesizer/surge-synthesizer.github.io | C | pnpm-lock.yaml | — | pnpm@10.30.3 | 2022-03 to 2022-08 | 0/0 |
| FleetAdmiralJakob/Portfolio | D | pnpm-lock.yaml | — | — | 2023-10 to 2024-03 | 0/0 |
| sledilnik/website | D | yarn.lock | 11.13.0 | — | 2021-03 to 2021-08 | 0/0 |
| aermin/ghChat | E | package-lock.json | — | — | 2018-11 to 2019-04 | 0/0 |
| ifmeorg/ifme | E | yarn.lock | 22 | — | 2016-05 to 2016-10 | 0/0 |
| jp-quintana/react-shopping-cart | E | package-lock.json | — | — | 2022-09 to 2023-02 | 0/0 |
| JustArchiNET/ASF-ui | E | package-lock.json | — | — | 2018-09 to 2019-02 | 0/0 |
| logotip4ik/portfolio | E | yarn.lock | — | yarn@3.6.0 | 2022-05 to 2022-10 | 0/0 |
| mydraft-cc/ui | E | package-lock.json | — | — | 2018-02 to 2018-07 | 0/0 |
Buckets: **A** Next.js+Tailwind · **B** Vite/React+Tailwind · **C** Astro+Tailwind · **D** Bootstrap · **E** plain CSS/SCSS.

## Output — three files

**`reprobe.json`** — one record per repository:

```json
{
  "repo": "owner/name",
  "bucket": "A",
  "commits": [
    {
      "sha": "",
      "date": "YYYY-MM-DD",
      "node_version_used": "v18.20.4",
      "node_rung": "declared | inferred_by_date",
      "pm_used": "pnpm@8.15.6",
      "pm_rung": "declared | lockfile_version | inferred_by_date",
      "install_ok": true,
      "build_ok": true,
      "install_seconds": 0,
      "build_seconds": 0,
      "failure_stage": "install | build | timeout | environment | null",
      "error_excerpt": "last 5 lines verbatim, or null"
    }
  ],
  "install_ok_count": 0,
  "build_ok_count": 0,
  "median_build_seconds": 0,
  "oldest_commit_builds": true,
  "all_rungs_declared": false,
  "new_verdict": "usable | usable_inferred | slow | broken | environment_incomplete",
  "changed_from_previous": true,
  "what_the_old_probe_got_wrong": "one sentence, or null if the old verdict stands"
}
```

Verdict rules — apply literally:

- **`usable`** — 6/6 install, 6/6 build, median build under 60s, **and every rung `declared`**.
- **`usable_inferred`** — same, but at least one version was inferred rather than declared.
- **`slow`** — builds 6/6 but median build 60s or more.
- **`broken`** — fewer than 6/6 on install or build, under a correctly resolved toolchain.
- **`environment_incomplete`** — your environment prevented a clean test. **Not the same as
  broken.** Use it and say why.

**`summary.json`** — counts before and after: how many changed verdict, broken→usable,
broken→usable_inferred, still broken; the same split **per bucket**; and the count of repositories
whose failures were purely toolchain. **Bucket A is the one I care about most** — 20 Next.js
repositories were probed last time and zero survived, and I need to know whether that is real.

**`toolchain_log.json`** — every distinct (Node, package manager) pair you activated, how you
obtained it, and any you could not obtain.

## Rules

- **Never report a build you did not run.** Every number must come from a command that executed.
- **Environment failures are not repository failures.** Missing system libraries, sandbox
  permission errors, a missing Rust or Python toolchain, registry outages — all `environment`,
  never `build`. The previous run got this right and it is why its numbers were usable.
- **Verbatim error excerpts**, five real lines. The specific text is how I tell a toolchain
  problem from a genuine one.
- **Report unchanged verdicts honestly.** If a repository is still broken under its own
  contemporary toolchain, that is the most valuable finding in this run — it means the previous
  result was right and I can stop doubting it. Do not manufacture improvements.
- No analysis or recommendations. Return the three JSON files.
