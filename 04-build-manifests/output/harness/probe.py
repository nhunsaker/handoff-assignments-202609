#!/usr/bin/env python3
"""
probe.py — build-manifest probe harness (Assignment 04).

Walks every page-touching commit in a repository's densest six-month window,
resolves a date-matched Node + package-manager toolchain per commit, installs,
builds, times both, counts routes, and writes an incremental manifest.

Subcommands:
  window    --repo <url|path> --workdir <dir> [--out window.json]
  probe-one --workdir <dir> --sha <sha>            (prints one per-commit record)
  manifest  --repo owner/name --stack <s> --workdir <dir> --window "YYYY-MM to YYYY-MM"
            --shas <f|sha1,sha2,...> --out manifest.json [--resume]

Environment knobs (defaults suit the machine this was built on; override as needed):
  FNM_DIR, FNM_BIN (~/.local/bin/fnm), COREPACK_HOME, NPM_PIN_DIR,
  PM_BIN_DIR (dir holding corepack shims; put it on PATH yourself or via harness).

Toolchain ladder (Phase 2), implemented in resolve_node() / resolve_pm():
  Node: .nvmrc | .node-version | engines.node at the commit -> "declared";
        else latest LTS released on/before the commit date -> "inferred_by_date".
        LTS majors by start date: v12 2019-10, v14 2020-10, v16 2021-10,
        v18 2022-10, v20 2023-10, v22 2024-10, v24 2025-10.
        A range like "^22 || ^24" resolves to the LOWEST satisfying version.
  PM:   packageManager in package.json (via corepack) -> "declared";
        else the lockfile's own format version -> "lockfile_version"
          package-lock.json lockfileVersion 1 -> npm 6, 2 -> npm 7/8, 3 -> npm 9+
          pnpm-lock.yaml  lockfileVersion 5.3 -> pnpm 6, 5.4 -> pnpm 7,
                          6.0 -> pnpm 8, 9.0 -> pnpm 9/10
          yarn.lock with __metadata: block -> yarn berry, without -> yarn 1
        within the implied major, the latest release on/before the commit date
        (still rung "lockfile_version"); no version field at all -> latest-at-date,
        rung "inferred_by_date".
"""
import argparse
import base64
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request

# ---------------------------------------------------------------- configuration

HOME = os.path.expanduser("~")
FNM_DIR = os.environ.get("FNM_DIR", os.path.join(HOME, ".fnm"))
FNM_BIN = os.environ.get("FNM_BIN", os.path.join(HOME, ".local", "bin", "fnm"))
COREPACK_HOME = os.environ.get("COREPACK_HOME",
                               os.path.join(HOME, ".cache", "node", "corepack"))
PM_BIN_DIR = os.environ.get("PM_BIN_DIR", os.path.join(HOME, ".local", "bin"))
NPM_PIN_DIR = os.environ.get("NPM_PIN_DIR", os.path.join(HOME, ".npm-pinned"))
INSTALL_TIMEOUT = 300
BUILD_TIMEOUT = 300
WINDOW_CAP = 150

LTS_STARTS = [(12, "2019-10"), (14, "2020-10"), (16, "2021-10"), (18, "2022-10"),
              (20, "2023-10"), (22, "2024-10"), (24, "2025-10")]
NODE_RELEASE_INDEX = "https://nodejs.org/download/release/index.json"

PAGE_PATTERNS = ["*.html", "*.astro", "*.vue", "*.svelte", "*.jsx", "*.tsx",
                 "*.css", "*.scss", "tailwind.config.*", "pages/", "app/",
                 "src/pages/", "content/", "_posts/"]

ENV_FAILURE_RES = [
    r"EPERM", r"EACCES", r"operation not permitted", r"permission denied",
    r"ENOTFOUND", r"EAI_AGAIN", r"ETIMEDOUT", r"ENETUNREACH", r"EHOSTUNREACH",
    r"No space left on device", r"ENOSPC", r"registry.*\b5\d\d\b",
    r"error downloading", r"Failed to download", r"network.*unreachable",
    r"unable to get local issuer certificate",
]

# ---------------------------------------------------------------- utilities

def sh(cmd, cwd=None, env=None, timeout=None, check=False):
    e = dict(os.environ)
    e["PATH"] = PM_BIN_DIR + os.pathsep + os.path.dirname(FNM_BIN) + \
        os.pathsep + e.get("PATH", "")
    e["FNM_DIR"] = FNM_DIR
    e["COREPACK_HOME"] = COREPACK_HOME
    e["COREPACK_ENABLE_STRICT"] = "0"
    if env:
        e.update(env)
    p = subprocess.run(cmd, cwd=cwd, env=e, shell=isinstance(cmd, str),
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       timeout=timeout, text=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"command failed ({p.returncode}): {cmd}\n{p.stdout[-2000:]}")
    return p


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "probe-harness"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


_node_releases = None

def node_releases():
    global _node_releases
    if _node_releases is None:
        _node_releases = fetch_json(NODE_RELEASE_INDEX)
    return _node_releases


def ver_tuple(v):
    v = v.lstrip("v")
    parts = re.split(r"[.\-+]", v)[:3]
    return tuple(int(x) if x.isdigit() else 0 for x in parts)


def ensure_node(version):
    """version like 'v20.20.2'. Install via fnm if missing."""
    r = sh([FNM_BIN, "ls"])
    if version in r.stdout or version.lstrip("v") in r.stdout:
        return version
    r = sh([FNM_BIN, "install", version])
    if r.returncode != 0:
        raise RuntimeError(f"fnm install {version} failed:\n{r.stdout[-1500:]}")
    return version


def node_cmd(version):
    """Prefix list that runs a command under the given node version."""
    return [FNM_BIN, "exec", "--using=" + version]


_npm_times = {}

def npm_time(pkg):
    """{version: date} for an npm package, from registry metadata (cached)."""
    if pkg not in _npm_times:
        data = fetch_json(f"https://registry.npmjs.org/{pkg}")
        times = data.get("time", {})
        times.pop("created", None)
        times.pop("modified", None)
        _npm_times[pkg] = times
    return _npm_times[pkg]


def latest_at_or_before(times, date_str, major=None):
    """Latest version in `times` (dict version->YYYY-MM-DD...) with date <= date_str,
    optionally restricted to a major. Returns None if nothing qualifies."""
    best, best_t = None, None
    for v, t in times.items():
        d = t[:10]
        if d > date_str:
            continue
        if major is not None and ver_tuple(v)[0] != major:
            continue
        if best is None or ver_tuple(v) > ver_tuple(best):
            best, best_t = v, d
    return best

# ---------------------------------------------------------------- toolchain ladder

LTS_NAMES = {"erbium": 12, "fermium": 14, "gallium": 16, "hydrogen": 18,
             "iron": 20, "krypton": 22, "": 24}


def min_satisfying(alt):
    """Lowest version satisfying one '||' alternative of an engines range.
    Handles: exact, '1.2.3', '^1.2.3', '~1.2.3', '>=1.2.3', '>1.2.3', '1.x', '1'."""
    alt = alt.strip()
    m = re.match(r"^[v=\s]*(\d+)(?:\.(\d+|x))?(?:\.(\d+|x))?", alt)
    if not m:
        return None
    major = int(m.group(1))
    minor = 0 if m.group(2) in (None, "x") else int(m.group(2))
    patch = 0 if m.group(3) in (None, "x") else int(m.group(3))
    if alt.lstrip().startswith(">") and not alt.lstrip().startswith(">="):
        patch += 1  # >1.2.3 -> lowest satisfying is 1.2.4 (approximation)
    return f"v{major}.{minor}.{patch}"


def resolve_node(tree_dir, commit_date):
    """Return (node_version, rung). Reads .nvmrc / .node-version / engines.node
    from the checked-out tree; else latest LTS on/before commit_date."""
    for name in (".nvmrc", ".node-version"):
        p = os.path.join(tree_dir, name)
        if os.path.isfile(p):
            raw = open(p).read().strip().strip("v")
            low = raw.lower()
            if low.startswith("lts/"):
                major = LTS_NAMES.get(low[4:], 24)
                v = latest_at_or_before(
                    {r["version"]: r["date"] for r in node_releases()},
                    commit_date, major=major)
                return ensure_node(v or f"v{major}.0.0"), "declared"
            if re.fullmatch(r"\d+", raw):
                major = int(raw)
                v = latest_at_or_before(
                    {r["version"]: r["date"] for r in node_releases()},
                    commit_date, major=major)
                return ensure_node(v or f"v{major}.0.0"), "declared"
            return ensure_node("v" + raw), "declared"
    pj = os.path.join(tree_dir, "package.json")
    if os.path.isfile(pj):
        try:
            engines = json.load(open(pj)).get("engines", {}).get("node")
        except Exception:
            engines = None
        if engines:
            cands = [min_satisfying(a) for a in str(engines).split("||")]
            cands = [c for c in cands if c]
            if cands:
                return ensure_node(sorted(cands, key=ver_tuple)[0]), "declared"
    # inferred: latest LTS whose start date precedes the commit
    major = 12
    for m, start in LTS_STARTS:
        if start <= commit_date[:7]:
            major = m
    times = {r["version"]: r["date"] for r in node_releases()}
    v = latest_at_or_before(times, commit_date, major=major)
    return ensure_node(v or f"v{major}.0.0"), "inferred_by_date"


def lockfile_kind(tree_dir):
    pj = os.path.join(tree_dir, "package.json")
    pkg = json.load(open(pj)) if os.path.isfile(pj) else {}
    if os.path.isfile(os.path.join(tree_dir, "package-lock.json")):
        try:
            lv = json.load(open(os.path.join(tree_dir, "package-lock.json")) \
                             ).get("lockfileVersion")
        except Exception:
            lv = None
        return ("npm", {1: 6, 2: 7, 3: 9}.get(lv), lv,
                pkg.get("packageManager"))
    if os.path.isfile(os.path.join(tree_dir, "pnpm-lock.yaml")):
        txt = open(os.path.join(tree_dir, "pnpm-lock.yaml")).read(4000)
        m = re.search(r"lockfileVersion:\s*['\"]?([\d.]+)", txt)
        lv = m.group(1) if m else None
        return ("pnpm", {"5.3": 6, "5.4": 7, "6.0": 8, "9.0": 9}.get(lv), lv,
                pkg.get("packageManager"))
    if os.path.isfile(os.path.join(tree_dir, "yarn.lock")):
        txt = open(os.path.join(tree_dir, "yarn.lock")).read(4000)
        berry = "__metadata:" in txt
        return ("yarn", None, ("berry" if berry else "classic"),
                pkg.get("packageManager"))
    return (None, None, None, pkg.get("packageManager"))


def ensure_pnpm_or_yarn(spec):
    """Activate name@version via corepack; return the command name."""
    r = sh(["corepack", "prepare", spec, "--activate"])
    if r.returncode != 0:
        raise RuntimeError(f"corepack prepare {spec} failed:\n{r.stdout[-1500:]}")
    return spec.split("@")[0]


def ensure_npm(version):
    """Install npm@version into a private prefix; return its binary path."""
    dest = os.path.join(NPM_PIN_DIR, version, "bin", "npm")
    if os.path.isfile(dest):
        return dest
    prefix = os.path.join(NPM_PIN_DIR, version)
    r = sh(["npm", "install", "-g", f"npm@{version}", "--prefix", prefix])
    if r.returncode != 0 or not os.path.isfile(dest):
        raise RuntimeError(f"npm i -g npm@{version} failed:\n{r.stdout[-1500:]}")
    return dest


def resolve_pm(tree_dir, commit_date):
    """Return (pm_kind, pm_cmd, pm_label, rung).
    pm_kind in npm|pnpm|yarn; pm_cmd is argv prefix list; pm_label like 'pnpm@9.15.0'."""
    kind, implied_major, lockver, pm_field = lockfile_kind(tree_dir)
    if kind is None:
        raise RuntimeError("no lockfile in tree")
    if pm_field:
        spec = re.split(r"\+", str(pm_field).strip())[0]  # strip +sha1/... hash
        name = spec.split("@")[0]
        if name == "npm":
            cmd = [ensure_npm(spec.split("@")[1])]
        else:
            ensure_pnpm_or_yarn(spec)
            cmd = [name]
        return kind, cmd, spec, "declared"
    if kind == "npm":
        major = implied_major or 6
        v = latest_at_or_before(npm_time("npm"), commit_date, major=major)
        if v is None:
            v = latest_at_or_before(npm_time("npm"), commit_date)
            return kind, [ensure_npm(v)], f"npm@{v}", "inferred_by_date"
        return kind, [ensure_npm(v)], f"npm@{v}", "lockfile_version"
    if kind == "pnpm":
        if implied_major is None:
            v = latest_at_or_before(npm_time("pnpm"), commit_date)
            ensure_pnpm_or_yarn(f"pnpm@{v}")
            return kind, ["pnpm"], f"pnpm@{v}", "inferred_by_date"
        v = latest_at_or_before(npm_time("pnpm"), commit_date, major=implied_major)
        if v is None:
            raise RuntimeError(f"no pnpm {implied_major}.x released by {commit_date}")
        ensure_pnpm_or_yarn(f"pnpm@{v}")
        return kind, ["pnpm"], f"pnpm@{v}", "lockfile_version"
    # yarn
    if lockver == "berry":
        v = latest_at_or_before(npm_time("yarn"), commit_date)
        # skip 1.x line for berry
        if v is not None and ver_tuple(v)[0] < 2:
            cands = {vv: tt for vv, tt in npm_time("yarn").items()
                     if ver_tuple(vv)[0] >= 2}
            v = latest_at_or_before(cands, commit_date)
        ensure_pnpm_or_yarn(f"yarn@{v}")
        return kind, ["yarn"], f"yarn@{v}", "lockfile_version"
    v = latest_at_or_before(npm_time("yarn"), commit_date, major=1)
    if v is None:
        v = latest_at_or_before(npm_time("yarn"), commit_date)
        ensure_pnpm_or_yarn(f"yarn@{v}")
        return kind, ["yarn"], f"yarn@{v}", "inferred_by_date"
    ensure_pnpm_or_yarn(f"yarn@{v}")
    return kind, ["yarn"], f"yarn@{v}", "lockfile_version"

# ---------------------------------------------------------------- probing

def checkout_clean(workdir, sha):
    sh(["git", "checkout", "-f", sha], cwd=workdir, check=True)
    sh(["git", "reset", "--hard"], cwd=workdir, check=True)
    sh(["git", "clean", "-fdx"], cwd=workdir, check=True)


def commit_date(workdir, sha):
    r = sh(["git", "show", "-s", "--format=%ad", "--date=short", sha], cwd=workdir)
    return r.stdout.strip()


def commit_subject(workdir, sha):
    r = sh(["git", "show", "-s", "--format=%s", sha], cwd=workdir)
    return r.stdout.strip().splitlines()[0] if r.stdout.strip() else ""


def page_file_match(path):
    for pat in PAGE_PATTERNS:
        if pat.endswith("/"):
            if path.startswith(pat) or ("/" + pat) in ("/" + path):
                return True
        elif pat.startswith("*."):
            if path.endswith(pat[1:]):
                return True
        else:  # tailwind.config.*
            if os.path.basename(path).startswith("tailwind.config."):
                return True
    return False


def diff_stat(workdir, sha):
    r = sh(["git", "show", "--pretty=format:", "--name-only", sha], cwd=workdir)
    files = [l for l in r.stdout.splitlines() if l.strip()]
    return files, [f for f in files if page_file_match(f)]


def is_env_failure(text):
    return any(re.search(p, text, re.I) for p in ENV_FAILURE_RES)


def last_lines(text, n=5):
    lines = [l for l in text.splitlines() if l.strip()]
    return "\n".join(lines[-n:]) if lines else ""


def detect_framework(tree_dir):
    files = set(os.listdir(tree_dir))
    if "astro.config.mjs" in files or "astro.config.ts" in files or \
            "astro.config.js" in files:
        return "astro"
    if "next.config.js" in files or "next.config.mjs" in files or \
            "next.config.ts" in files:
        return "next"
    if "eleventy.config.js" in files or ".eleventy.js" in files or \
            "_config.yml" in files and os.path.isfile(
                os.path.join(tree_dir, ".eleventy.js")):
        return "eleventy"
    if "vite.config.js" in files or "vite.config.ts" in files or \
            "vite.config.mjs" in files:
        return "vite"
    return "unknown"


def count_routes(tree_dir):
    """Count built pages. Returns (count, method)."""
    fw = detect_framework(tree_dir)
    if fw == "next":
        app_pages = []
        for root, _d, fs in os.walk(os.path.join(tree_dir, ".next", "server", "app")):
            app_pages += [f for f in fs if f == "page.js"]
        if app_pages or os.path.isdir(os.path.join(tree_dir, ".next", "server", "app")):
            return len(app_pages), \
                "counted .next/server/app/**/page.js (Next.js app router)"
        out = os.path.join(tree_dir, "out")
        if os.path.isdir(out):
            n = sum(1 for _r, _d, fs in os.walk(out)
                    for f in fs if f.endswith(".html"))
            return n, "counted .html files under out/ (Next.js static export)"
        pages = os.path.join(tree_dir, ".next", "server", "pages")
        n = sum(1 for _r, _d, fs in os.walk(pages)
                for f in fs if f.endswith(".html")) if os.path.isdir(pages) else 0
        return n, "counted .html files under .next/server/pages/ (Next.js pages router)"
    if fw == "eleventy":
        site = os.path.join(tree_dir, "_site")
        n = sum(1 for _r, _d, fs in os.walk(site)
                for f in fs if f.endswith(".html")) if os.path.isdir(site) else 0
        return n, "counted .html files under _site/ (Eleventy)"
    for d in ("dist", "out", "build"):
        p = os.path.join(tree_dir, d)
        if os.path.isdir(p):
            n = sum(1 for _r, _dd, fs in os.walk(p)
                    for f in fs if f.endswith(".html"))
            return n, f"counted .html files under {d}/ ({fw})"
    return 0, f"no recognised build output dir found (framework={fw})"


def probe_one(workdir, sha):
    """Full per-commit probe. Returns the per-commit record dict."""
    rec = {"sha": sha}
    try:
        checkout_clean(workdir, sha)
    except Exception as e:
        rec.update({"date": None, "subject": "", "files_changed": 0,
                    "page_files_changed": [], "node_used": None,
                    "node_rung": None, "pm_used": None, "pm_rung": None,
                    "install_ok": False, "install_seconds": 0,
                    "build_ok": False, "build_seconds": 0,
                    "route_count": 0, "route_count_method": "",
                    "failure_stage": "environment",
                    "error_excerpt": last_lines(str(e))})
        return rec
    date = commit_date(workdir, sha)
    rec["date"] = date
    rec["subject"] = commit_subject(workdir, sha)
    files, page_files = diff_stat(workdir, sha)
    rec["files_changed"] = len(files)
    rec["page_files_changed"] = page_files
    # toolchain
    try:
        node_ver, node_rung = resolve_node(workdir, date)
        kind, pm_cmd, pm_label, pm_rung = resolve_pm(workdir, date)
    except Exception as e:
        rec.update({"node_used": None, "node_rung": None, "pm_used": None,
                    "pm_rung": None, "install_ok": False, "install_seconds": 0,
                    "build_ok": False, "build_seconds": 0, "route_count": 0,
                    "route_count_method": "",
                    "failure_stage": "environment" if is_env_failure(str(e))
                    else "install", "error_excerpt": last_lines(str(e))})
        return rec
    rec["node_used"] = node_ver
    rec["node_rung"] = node_rung
    rec["pm_used"] = pm_label
    rec["pm_rung"] = pm_rung
    pj = os.path.join(workdir, "package.json")
    try:
        build_script = json.load(open(pj)).get("scripts", {}).get("build")
    except Exception:
        build_script = None
    ncmd = node_cmd(node_ver)
    # install
    if kind == "npm":
        install_argv = pm_cmd + ["ci", "--no-audit", "--no-fund"]
    elif kind == "pnpm":
        install_argv = pm_cmd + ["install", "--frozen-lockfile",
                                 "--ignore-workspace"]
    else:
        install_argv = pm_cmd + ["install", "--frozen-lockfile"]
    t0 = time.time()
    try:
        r = sh(ncmd + install_argv, cwd=workdir, timeout=INSTALL_TIMEOUT)
        install_s = time.time() - t0
        install_ok = (r.returncode == 0)
        install_out = r.stdout
    except subprocess.TimeoutExpired as e:
        install_s = INSTALL_TIMEOUT
        install_ok = False
        install_out = (e.stdout or "") if isinstance(e.stdout, str) else ""
        rec.update({"install_ok": False, "install_seconds": int(install_s),
                    "build_ok": False, "build_seconds": 0, "route_count": 0,
                    "route_count_method": "",
                    "failure_stage": "environment" if is_env_failure(install_out)
                    else "timeout", "error_excerpt": last_lines(install_out)})
        return rec
    rec["install_ok"] = install_ok
    rec["install_seconds"] = int(install_s)
    if not install_ok:
        rec.update({"build_ok": False, "build_seconds": 0, "route_count": 0,
                    "route_count_method": "",
                    "failure_stage": "environment" if is_env_failure(install_out)
                    else "install", "error_excerpt": last_lines(install_out)})
        return rec
    if not build_script:
        rec.update({"build_ok": False, "build_seconds": 0, "route_count": 0,
                    "route_count_method": "",
                    "failure_stage": "build",
                    "error_excerpt": "no build script in package.json"})
        return rec
    # build
    t0 = time.time()
    try:
        r = sh(ncmd + pm_cmd + ["run", "build"], cwd=workdir,
               timeout=BUILD_TIMEOUT)
        build_s = time.time() - t0
        build_ok = (r.returncode == 0)
        build_out = r.stdout
    except subprocess.TimeoutExpired as e:
        build_s = BUILD_TIMEOUT
        build_ok = False
        build_out = (e.stdout or "") if isinstance(e.stdout, str) else ""
        rec.update({"build_ok": False, "build_seconds": int(build_s),
                    "route_count": 0, "route_count_method": "",
                    "failure_stage": "environment" if is_env_failure(build_out)
                    else "timeout", "error_excerpt": last_lines(build_out)})
        return rec
    rec["build_ok"] = build_ok
    rec["build_seconds"] = int(build_s)
    if not build_ok:
        rec.update({"route_count": 0, "route_count_method": "",
                    "failure_stage": "environment" if is_env_failure(build_out)
                    else "build", "error_excerpt": last_lines(build_out)})
        return rec
    n_routes, method = count_routes(workdir)
    rec.update({"route_count": n_routes, "route_count_method": method,
                "failure_stage": None, "error_excerpt": None})
    return rec

# ---------------------------------------------------------------- window selection

def page_touching_commits(workdir):
    """[(sha, date)] for commits touching page files, oldest first."""
    r = sh(["git", "log", "--format=%H %ad", "--date=short", "--reverse", "--"]
           + PAGE_PATTERNS, cwd=workdir, check=True)
    out = []
    for line in r.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            out.append((parts[0], parts[1]))
    return out


def has_package_json(workdir, sha):
    r = sh(["git", "cat-file", "-e", f"{sha}:package.json"], cwd=workdir)
    return r.returncode == 0


def has_lockfile(workdir, sha):
    for f in ("package-lock.json", "pnpm-lock.yaml", "yarn.lock"):
        r = sh(["git", "cat-file", "-e", f"{sha}:{f}"], cwd=workdir)
        if r.returncode == 0:
            return True
    return False


def densest_window(workdir):
    """Densest 6-month window of page-touching commits, requiring package.json
    AND a lockfile at every commit.

    Rationale (extension of the assignment's own Phase 1 correction): the
    correction slides the window past spans with no package.json because such
    history has "nothing to build". A span with no lockfile likewise has
    nothing to *reproducibly* build — installing without a lockfile resolves
    today's dependency versions, which Assignment 01 excludes outright as
    defeating the entire purpose. Such commits are unprobable, not broken,
    so they are excluded from the window rather than scored as failures.
    Returns (window_label, [(sha, date)], capped)."""
    commits = [(s, d) for s, d in page_touching_commits(workdir)
               if has_package_json(workdir, s) and has_lockfile(workdir, s)]
    if not commits:
        return None, [], False
    months = sorted({d[:7] for _, d in commits})
    best, best_list = None, []
    for start in months:
        y, m = int(start[:4]), int(start[5:7])
        end_m = m + 5
        end = f"{y + (end_m - 1) // 12:04d}-{(end_m - 1) % 12 + 1:02d}"
        inside = [(s, d) for s, d in commits if start <= d[:7] <= end]
        if len(inside) > len(best_list):
            best, best_list = (f"{start} to {end}"), inside
    capped = False
    if len(best_list) > WINDOW_CAP:
        best_list = sorted(best_list, key=lambda x: x[1])[-WINDOW_CAP:]
        capped = True
    best_list = sorted(best_list, key=lambda x: x[1])  # chronological
    return best, best_list, capped


# ---------------------------------------------------------------- manifest

def percentile(xs, p):
    if not xs:
        return 0
    xs = sorted(xs)
    k = (len(xs) - 1) * p / 100
    f, c = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def median(xs):
    return percentile(xs, 50)


def longest_buildable_run(commits):
    best = cur = 0
    for c in commits:
        if c.get("build_ok"):
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def verdict_for(commits):
    n = len(commits)
    if n == 0:
        return "environment_incomplete"
    env = sum(1 for c in commits if c.get("failure_stage") == "environment")
    if env > n / 2:
        return "environment_incomplete"
    rate = sum(1 for c in commits if c.get("build_ok")) / n
    builds = [c["build_seconds"] for c in commits if c.get("build_ok")]
    med = median(builds)
    all_declared = all(c.get("node_rung") == "declared" and
                       c.get("pm_rung") == "declared" for c in commits)
    if rate >= 0.90 and med < 60 and all_declared:
        return "usable"
    if rate >= 0.90 and med < 60:
        return "usable_inferred"
    if rate >= 0.90:
        return "slow"
    return "broken"


def build_summary(repo, stack, window, shas, commits, capped):
    ok = [c for c in commits if c.get("build_ok")]
    builds = [c["build_seconds"] for c in ok]
    routes = [c["route_count"] for c in ok]
    per_month = {}
    for c in commits:
        if c.get("build_ok") and c.get("date"):
            m = c["date"][:7]
            per_month[m] = per_month.get(m, 0) + 1
    return {
        "repo": repo, "stack": stack, "window": window,
        "commits_in_window": len(shas), "commits_probed": len(commits),
        "capped": capped, "commits": commits,
        "summary": {
            "install_ok": sum(1 for c in commits if c.get("install_ok")),
            "build_ok": len(ok),
            "environment": sum(1 for c in commits
                               if c.get("failure_stage") == "environment"),
            "build_ok_rate": round(len(ok) / len(commits), 4) if commits else 0.0,
            "median_build_seconds": round(median(builds), 1),
            "p90_build_seconds": round(percentile(builds, 90), 1),
            "all_rungs_declared_count": sum(
                1 for c in commits
                if c.get("node_rung") == "declared" and c.get("pm_rung") == "declared"),
            "route_count_min": min(routes) if routes else 0,
            "route_count_median": round(median(routes), 1) if routes else 0,
            "route_count_max": max(routes) if routes else 0,
            "buildable_commits_per_month": [
                {"month": m, "count": per_month[m]} for m in sorted(per_month)],
            "longest_run_of_consecutive_buildable_commits":
                longest_buildable_run(commits),
            "verdict": verdict_for(commits),
        },
    }


def run_manifest(repo, stack, workdir, window, shas, out_path, resume=False):
    commits = []
    done = set()
    if resume and os.path.isfile(out_path):
        try:
            old = json.load(open(out_path))
            commits = old.get("commits", [])
            done = {c["sha"] for c in commits}
            print(f"resuming: {len(done)} commits already probed", flush=True)
        except Exception as e:
            print(f"resume read failed ({e}); starting fresh", flush=True)
    for i, sha in enumerate(shas):
        if sha in done:
            continue
        print(f"[{i + 1}/{len(shas)}] probing {sha[:8]}", flush=True)
        try:
            rec = probe_one(workdir, sha)
        except Exception as e:  # never lose the manifest to a harness crash
            rec = {"sha": sha, "date": None, "subject": "",
                   "files_changed": 0, "page_files_changed": [],
                   "node_used": None, "node_rung": None, "pm_used": None,
                   "pm_rung": None, "install_ok": False, "install_seconds": 0,
                   "build_ok": False, "build_seconds": 0, "route_count": 0,
                   "route_count_method": "",
                   "failure_stage": "environment",
                   "error_excerpt": last_lines(str(e))}
        commits.append(rec)
        # incremental write after EVERY commit — a crash keeps progress
        man = build_summary(repo, stack, window, shas, commits,
                            capped=len(shas) == WINDOW_CAP)
        tmp = out_path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(man, f, indent=1)
        os.replace(tmp, out_path)
    man = build_summary(repo, stack, window, shas, commits,
                        capped=len(shas) == WINDOW_CAP)
    with open(out_path, "w") as f:
        json.dump(man, f, indent=1)
    print(f"wrote {out_path}: verdict={man['summary']['verdict']} "
          f"build_ok={man['summary']['build_ok']}/{len(commits)}", flush=True)
    return man


# ---------------------------------------------------------------- CLI

def main():
    ap = argparse.ArgumentParser(description="Assignment 04 build-manifest probe")
    sub = ap.add_subparsers(dest="cmd", required=True)

    w = sub.add_parser("window", help="find densest 6-month window")
    w.add_argument("--repo", required=True)
    w.add_argument("--workdir", required=True)
    w.add_argument("--out", default=None)

    p = sub.add_parser("probe-one", help="probe a single commit")
    p.add_argument("--workdir", required=True)
    p.add_argument("--sha", required=True)

    m = sub.add_parser("manifest", help="probe every commit, write manifest")
    m.add_argument("--repo", required=True)
    m.add_argument("--stack", required=True)
    m.add_argument("--workdir", required=True)
    m.add_argument("--window", required=True)
    m.add_argument("--shas", required=True,
                   help="'a,b,c' or @file with one sha per line")
    m.add_argument("--out", required=True)
    m.add_argument("--resume", action="store_true")

    args = ap.parse_args()
    if args.cmd == "window":
        wd = args.workdir
        if not os.path.isdir(os.path.join(wd, ".git")):
            sh(["git", "clone", args.repo, wd], check=True)
        else:
            sh(["git", "fetch", "origin"], cwd=wd)
        window, commits, capped = densest_window(wd)
        result = {"repo": args.repo, "window": window, "capped": capped,
                  "commits_in_window": len(commits),
                  "shas": [s for s, _ in commits],
                  "sha_dates": {s: d for s, d in commits}}
        print(json.dumps(result, indent=1))
        if args.out:
            json.dump(result, open(args.out, "w"), indent=1)
    elif args.cmd == "probe-one":
        print(json.dumps(probe_one(args.workdir, args.sha), indent=1))
    elif args.cmd == "manifest":
        if args.shas.startswith("@"):
            shas = [l.strip() for l in open(args.shas[1:])
                    if l.strip()]
        else:
            shas = [s.strip() for s in args.shas.split(",") if s.strip()]
        man = run_manifest(args.repo, args.stack, args.workdir, args.window,
                           shas, args.out, resume=args.resume)
        print(json.dumps(man["summary"], indent=1))


if __name__ == "__main__":
    main()
