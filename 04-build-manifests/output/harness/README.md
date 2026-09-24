# probe.py — build-manifest probe harness

Walks every page-touching commit in a repository's densest six-month window,
resolves a **date-matched** Node + package-manager toolchain per commit, installs,
builds, times both steps, counts the routes the build produced, and writes an
incremental manifest. A crash never loses probed commits: the manifest is
rewritten after every single commit, and `--resume` skips SHAs already probed.

## Requirements

- Python 3, git, curl
- A Node version manager exposing `fnm` (`FNM_BIN`, default `~/.local/bin/fnm`)
  with `FNM_DIR` (default `~/.fnm`)
- `corepack` with shims on `PATH` (`PM_BIN_DIR`, default `~/.local/bin`) and
  `COREPACK_HOME` set (default `~/.cache/node/corepack`)
- npm registry access (used to resolve "latest release on or before <date>")
- Env vars, all overridable: `FNM_DIR`, `FNM_BIN`, `COREPACK_HOME`,
  `PM_BIN_DIR`, `NPM_PIN_DIR` (where version-pinned npm copies live)

## Usage

Find the densest window (package.json AND a lockfile must exist at every commit
in it — a span with no lockfile has nothing to *reproducibly* build, so those
commits are excluded from the window rather than scored as failures):

```
python3 probe.py window --repo https://github.com/owner/name \
    --workdir /path/to/checkout --out window.json
```

Probe one commit (prints the per-commit record as JSON):

```
python3 probe.py probe-one --workdir /path/to/checkout --sha <sha>
```

Probe every commit and write the manifest (resumable):

```
python3 probe.py manifest --repo owner/name --stack "Next.js + Tailwind" \
    --workdir /path/to/checkout --window "2024-01 to 2024-06" \
    --shas @window_shas.txt --out manifest.json --resume
```

One worktree per repository; it is checked out and `git clean -fdx`'d per commit.

## The toolchain ladder

`resolve_node(tree, date)`:
1. `.nvmrc` / `.node-version` / `engines.node` **at that commit** → rung `declared`.
   Ranges resolve to the **lowest** satisfying version (`^22 || ^24` → `v22.0.0`).
2. Else the latest LTS released on or before the commit date → `inferred_by_date`
   (v12 2019-10 · v14 2020-10 · v16 2021-10 · v18 2022-10 · v20 2023-10 ·
   v22 2024-10 · v24 2025-10; latest patch of that major not newer than the commit,
   read from the Node release index).

`resolve_pm(tree, date)`:
1. `packageManager` in `package.json` at that commit, via corepack → `declared`
   (a `+sha1…`/`+sha512…` suffix is stripped before handing it to corepack).
2. Else the lockfile's own format version → `lockfile_version`:
   `package-lock.json` lockfileVersion 1→npm 6, 2→npm 7/8, 3→npm 9+;
   `pnpm-lock.yaml` 5.3→pnpm 6, 5.4→pnpm 7, 6.0→pnpm 8, 9.0→pnpm 9/10;
   `yarn.lock` with `__metadata:`→berry, without→yarn 1.
   Within the implied major, the latest release on or before the commit date
   (from registry `time` metadata).
3. No version field → latest-at-date, rung `inferred_by_date`.

Install honors the lockfile (`npm ci` / `pnpm install --frozen-lockfile
--ignore-workspace` / `yarn install --frozen-lockfile`); both steps are killed at
300 s. Output matching permission errors, DNS/registry failures, or disk-full is
classified `failure_stage: environment`, never as a build failure.

## Outputs

- Per-commit record: sha, date, subject, files_changed, page_files_changed,
  node_used/_rung, pm_used/_rung, install_ok/_seconds, build_ok/_seconds,
  route_count/_method, failure_stage, error_excerpt (last 5 lines, verbatim).
- Manifest: the commit records plus a summary block (install_ok, build_ok,
  environment, build_ok_rate, median/p90 build seconds, all_rungs_declared_count,
  route_count min/median/max, buildable_commits_per_month,
  longest_run_of_consecutive_buildable_commits, verdict).
- Route counting: `.html` under `dist/`/`out/`/`build/`/`_site/`; Next.js app
  router counts `.next/server/app/**/page.js`, static export counts `out/*.html`,
  pages router counts `.next/server/pages/*.html`. The method used is recorded
  per commit because it differs per framework.
