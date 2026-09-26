#!/usr/bin/env python3
"""Build worker: claim commits, build each with the date-matched toolchain (node v22.14.0, npm 10.9.2).

Usage: build_worker.py <worker_id>
State: scratch/build_state.json (flock-guarded): {"next": N, "commits": [sha,...]}.
Builds into scratch/builds/<sha12>/, writes .done or .failed markers, logs to scratch/build_logs/<sha12>.log.
"""
import sys, os, json, fcntl, subprocess, time, shutil

WID = sys.argv[1]
BASE = os.path.expanduser('~/workspace/handoff-assignments-202609/16-rendered-geometry-history')
SCR = os.path.join(BASE, 'scratch')
REPO = os.path.join(SCR, 'repos', 'tempertemper.git')
NODE_BIN = os.path.expanduser('~/.local/share/fnm/node-versions/v22.14.0/installation/bin')
ENV = dict(os.environ, PATH=NODE_BIN + ':' + os.environ['PATH'])


def claim():
    stf = os.path.join(SCR, 'build_state.json')
    with open(stf, 'r+') as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        st = json.load(fh)
        if st['next'] >= len(st['commits']):
            fcntl.flock(fh, fcntl.LOCK_UN)
            return None
        sha = st['commits'][st['next']]
        st['next'] += 1
        fh.seek(0); json.dump(st, fh); fh.truncate()
        fcntl.flock(fh, fcntl.LOCK_UN)
        return sha


def run(cmd, cwd, timeout=600):
    p = subprocess.run(cmd, cwd=cwd, env=ENV, capture_output=True, text=True, timeout=timeout)
    return p


def main():
    wt = os.path.join(SCR, 'wt_build_%s' % WID)
    if not os.path.exists(wt):
        r = run(['git', '-C', REPO, 'worktree', 'add', '--detach', wt, 'HEAD'], cwd=SCR)
        assert r.returncode == 0, r.stderr[-500:]
    while True:
        sha = claim()
        if sha is None:
            print('worker %s: no more commits' % WID, flush=True)
            return
        sha12 = sha[:12]
        bdir = os.path.join(SCR, 'builds', sha12)
        if os.path.exists(os.path.join(bdir, '.done')):
            continue
        logf = os.path.join(SCR, 'build_logs', sha12 + '.log')
        os.makedirs(os.path.dirname(logf), exist_ok=True)
        os.makedirs(bdir, exist_ok=True)
        t0 = time.time()
        log = open(logf, 'w')
        try:
            log.write('commit %s worker %s\n' % (sha, WID)); log.flush()
            r = run(['git', 'checkout', '-f', sha], cwd=wt)
            if r.returncode != 0:
                raise RuntimeError('checkout failed: ' + r.stderr[-800:])
            # remove previous build output and node_modules leftovers
            shutil.rmtree(os.path.join(wt, 'dist'), ignore_errors=True)
            r = run(['npm', 'ci', '--no-audit', '--no-fund'], cwd=wt, timeout=600)
            log.write('--- npm ci rc=%d (%.1fs)\n' % (r.returncode, time.time() - t0))
            log.write(r.stdout[-2000:] + '\n' + r.stderr[-2000:]); log.flush()
            if r.returncode != 0:
                raise RuntimeError('npm ci failed rc=%d' % r.returncode)
            r = run(['npm', 'run', 'build'], cwd=wt, timeout=600)
            secs = time.time() - t0
            log.write('--- npm run build rc=%d (%.1fs)\n' % (r.returncode, secs))
            log.write(r.stdout[-3000:] + '\n' + r.stderr[-3000:]); log.flush()
            if r.returncode != 0:
                raise RuntimeError('npm run build failed rc=%d' % r.returncode)
            dist = os.path.join(wt, 'dist')
            if not os.path.isdir(dist):
                raise RuntimeError('no dist/ produced')
            # move dist into place (atomic-ish per commit)
            dest = os.path.join(bdir, 'dist')
            shutil.rmtree(dest, ignore_errors=True)
            shutil.move(dist, dest)
            npages = sum(1 for dp, dn, fn in os.walk(dest) for f in fn if f.endswith('.html'))
            with open(os.path.join(bdir, '.done'), 'w') as fh:
                fh.write(json.dumps({'sha': sha, 'build_seconds': round(secs, 2),
                                     'html_pages': npages, 'worker': WID,
                                     'node': 'v22.14.0', 'npm': '10.9.2'}))
            print('worker %s built %s (%d pages, %.1fs)' % (WID, sha12, npages, secs), flush=True)
        except Exception as e:
            secs = time.time() - t0
            tb = traceback_lines(logf)
            with open(os.path.join(bdir, '.failed'), 'w') as fh:
                fh.write(json.dumps({'sha': sha, 'error': str(e)[:500],
                                     'error_kind': 'environment_incomplete',
                                     'error_excerpt': tb, 'worker': WID,
                                     'seconds': round(secs, 2)}))
            print('worker %s FAILED %s: %s' % (WID, sha12, str(e)[:200]), flush=True)
        finally:
            log.close()


def traceback_lines(logf):
    try:
        with open(logf) as fh:
            lines = fh.read().strip().splitlines()
        return lines[-5:] if len(lines) >= 5 else lines
    except Exception:
        return []


if __name__ == '__main__':
    main()
