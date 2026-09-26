#!/usr/bin/env python3
"""Orchestrator for assignment 16.

Phase A: build commit 1, render it fully (both viewports, with attrs),
         measure, decide drop flags (attrs? 390-nonlist?) to stay under 180MB.
Phase B: build commits 2..102, render with flags, enqueue as builds complete.
Then: deltas (phase 3), summary recompute, push.

State files (scratch/): build_state.json, render_state.json, results.jsonl,
flags.json, enqueued.json. Workers: scripts/build_worker.py (system python),
scripts/render_worker.py (venv python).
"""
import sys, os, json, fcntl, subprocess, time, shutil, datetime, gzip

BASE = os.path.expanduser('~/workspace/handoff-assignments-202609/16-rendered-geometry-history')
SCR = os.path.join(BASE, 'scratch')
OUT = os.path.join(BASE, 'output')
REPO = os.path.expanduser('~/workspace/handoff-assignments-202609')
VENV_PY = os.path.expanduser('~/workspace/a15-work/venv/bin/python')
VIEWPORTS = ['1280x800', '390x844']
CAP_BYTES = 180 * 1024 * 1024
LIST_RE = None
import re as _re
LIST_RE = _re.compile(r'^(index\.html|blog/index\.html|blog/year/[^/]+\.html|category/[^/]+\.html)$')

N_BUILD = 3
N_RENDER = 4

procs = []


def log(msg):
    ts = datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S')
    print('[%sZ] %s' % (ts, msg), flush=True)


def locked_json(path, fn, default=None):
    with open(path, 'r+') as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            st = json.load(fh)
        except Exception:
            st = default
        st = fn(st)
        fh.seek(0); json.dump(st, fh); fh.truncate()
        fcntl.flock(fh, fcntl.LOCK_UN)
        return st


def spawn(cmd, name):
    log('spawn %s: %s' % (name, ' '.join(cmd[:3])))
    p = subprocess.Popen(cmd, stdout=open(os.path.join(SCR, 'logs', name + '.out'), 'a'),
                         stderr=subprocess.STDOUT)
    procs.append((name, p))
    return p


def init_state():
    os.makedirs(os.path.join(SCR, 'logs'), exist_ok=True)
    commits = json.load(open(os.path.join(REPO, '10-build-history-diffs', 'output', 'commits',
                                          'tempertemper__www.tempertemper.net.json')))
    shas = [c['sha'] for c in commits]
    with open(os.path.join(SCR, 'build_state.json'), 'w') as fh:
        json.dump({'next': 0, 'commits': shas}, fh)
    with open(os.path.join(SCR, 'render_state.json'), 'w') as fh:
        json.dump({'next': 0, 'jobs': [], 'enqueued_all': False}, fh)
    with open(os.path.join(SCR, 'flags.json'), 'w') as fh:
        json.dump({'drop_attrs': False, 'drop_390_nonlist': False, 'decided': False}, fh)
    with open(os.path.join(SCR, 'enqueued.json'), 'w') as fh:
        json.dump([], fh)
    open(os.path.join(SCR, 'results.jsonl'), 'w').close()
    return shas


def enqueue_commit(sha12, full_sha):
    """Append render jobs for one built commit; returns job count."""
    pages = json.load(open(os.path.join(OUT, 'pages', sha12 + '.json')))['pages']
    flags = json.load(open(os.path.join(SCR, 'flags.json')))
    jobs = []
    for e in pages:
        for vp in VIEWPORTS:
            if flags['drop_390_nonlist'] and vp == '390x844' and not LIST_RE.match(e['page']):
                continue
            jobs.append({'sha12': sha12, 'full_sha': full_sha, 'page': e['page'], 'viewport': vp})
    def add(st):
        st['jobs'].extend(jobs)
        return st
    locked_json(os.path.join(SCR, 'render_state.json'), add, {'next': 0, 'jobs': []})
    def mark(lst):
        if sha12 not in lst:
            lst.append(sha12)
        return lst
    locked_json(os.path.join(SCR, 'enqueued.json'), mark, [])
    return len(jobs)


def results_for(sha12):
    n_ok = n_fail = 0
    bytes_sum = 0
    rf = os.path.join(SCR, 'results.jsonl')
    if not os.path.exists(rf):
        return 0, 0, 0
    with open(rf) as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get('sha12') != sha12:
                continue
            if r.get('ok'):
                n_ok += 1; bytes_sum += r.get('bytes', 0)
            else:
                n_fail += 1
    return n_ok, n_fail, bytes_sum


def decide_drops(sha12):
    """After commit-1 fully rendered: project total geometry size, set flags."""
    n_ok, n_fail, b1 = results_for(sha12)
    log('commit1 results: ok=%d fail=%d bytes=%d' % (n_ok, n_fail, b1))
    # per (page, viewport) bytes from commit-1 results; need path->bytes map
    per_page = {}
    with open(os.path.join(SCR, 'results.jsonl')) as fh:
        for line in fh:
            r = json.loads(line)
            if r.get('sha12') == sha12 and r.get('ok'):
                per_page[(r['page'], r['viewport'])] = r['bytes']
    vp_mean = {}
    for vp in VIEWPORTS:
        vals = [b for (p, v), b in per_page.items() if v == vp]
        vp_mean[vp] = sum(vals) / len(vals) if vals else 0
    log('commit1 mean bytes: 1280=%d 390=%d (n=%d)' % (vp_mean['1280x800'], vp_mean['390x844'], len(per_page)))
    # full job list projection
    total = 0
    total_no390nonlist = 0
    n_jobs = 0
    for pf in sorted(os.listdir(os.path.join(OUT, 'pages'))):
        d = json.load(open(os.path.join(OUT, 'pages', pf)))
        for e in d['pages']:
            for vp in VIEWPORTS:
                b = per_page.get((e['page'], vp), vp_mean[vp])
                total += b
                n_jobs += 1
                if not (vp == '390x844' and not LIST_RE.match(e['page'])):
                    total_no390nonlist += b
    log('projected total: %.1f MB over %d renders' % (total / 1048576, n_jobs))
    # attrs-strip ratio from a sample of commit-1 files
    import random
    sample = [(p, v) for (p, v) in per_page][:60]
    rb_with = rb_without = 0
    for (p, v) in sample:
        f = os.path.join(OUT, 'geometry', sha12, v, p.replace('/', '__') + '.json.gz')
        raw = gzip.open(f, 'rb').read()
        rb_with += len(raw)
        d = json.loads(raw)
        for e in d['elements']:
            e['attrs'] = {}
        rb_without += len(gzip.compress(json.dumps(d, separators=(',', ':')).encode()))
    ratio = rb_without / rb_with if rb_with else 1.0
    log('attrs-strip ratio: %.3f' % ratio)
    flags = {'drop_attrs': False, 'drop_390_nonlist': False, 'decided': True,
             'projected_bytes_with_attrs': int(total),
             'attrs_strip_ratio': round(ratio, 4)}
    if total > CAP_BYTES:
        flags['drop_attrs'] = True
        total2 = total * ratio
        flags['projected_bytes_no_attrs'] = int(total2)
        log('projected %.1fMB > 180MB -> dropping attrs (proj %.1fMB)' % (total / 1048576, total2 / 1048576))
        if total2 > CAP_BYTES:
            flags['drop_390_nonlist'] = True
            total3 = total_no390nonlist * ratio
            flags['projected_bytes_no_attrs_no390nonlist'] = int(total3)
            log('still > 180MB -> also dropping 390x844 for non-list pages (proj %.1fMB)' % (total3 / 1048576))
    with open(os.path.join(SCR, 'flags.json'), 'w') as fh:
        json.dump(flags, fh)
    return flags


def apply_drops_to_commit1(sha12, flags):
    """Make commit-1 files consistent with flags (strip attrs / delete 390 non-list)."""
    if flags['drop_attrs']:
        n = 0
        for vp in VIEWPORTS:
            d = os.path.join(OUT, 'geometry', sha12, vp)
            if not os.path.isdir(d):
                continue
            for fn in os.listdir(d):
                f = os.path.join(d, fn)
                raw = gzip.open(f, 'rb').read()
                rec = json.loads(raw)
                for e in rec['elements']:
                    e['attrs'] = {}
                with gzip.open(f, 'wb', compresslevel=6) as fh:
                    fh.write(json.dumps(rec, separators=(',', ':')).encode())
                n += 1
        log('stripped attrs from %d commit-1 files' % n)
    if flags['drop_390_nonlist']:
        n = 0
        d = os.path.join(OUT, 'geometry', sha12, '390x844')
        if os.path.isdir(d):
            for fn in os.listdir(d):
                page = fn[:-len('.json.gz')].replace('__', '/')
                if not LIST_RE.match(page):
                    os.remove(os.path.join(d, fn)); n += 1
        log('deleted %d commit-1 390x844 non-list files' % n)


def heal_missing_files():
    """Re-enqueue ok rows whose geometry file is missing (e.g. reboot wiped
    them). Removes the stale rows and appends fresh jobs. Returns count healed."""
    rf = os.path.join(SCR, 'results.jsonl')
    if not os.path.exists(rf):
        return 0
    missing = []
    seen = set()
    with open(rf) as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if not r.get('ok'):
                continue
            key = (r['sha12'], r['page'], r['viewport'])
            if key in seen:
                continue
            seen.add(key)
            f = os.path.join(OUT, 'geometry', r['sha12'], r['viewport'],
                             r['page'].replace('/', '__') + '.json.gz')
            if not os.path.exists(f):
                missing.append(r)
    if not missing:
        return 0
    log('heal: %d ok rows with missing files; re-enqueueing' % len(missing))
    mkeys = set((r['sha12'], r['page'], r['viewport']) for r in missing)
    with open(rf) as fh:
        lines = fh.readlines()
    with open(rf, 'w') as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        for line in lines:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get('ok') and (r['sha12'], r['page'], r['viewport']) in mkeys:
                continue
            fh.write(line)
        fcntl.flock(fh, fcntl.LOCK_UN)

    def add(st):
        for r in missing:
            st['jobs'].append({'sha12': r['sha12'],
                               'full_sha': r.get('commit', r.get('full_sha')),
                               'page': r['page'], 'viewport': r['viewport']})
        return st
    locked_json(os.path.join(SCR, 'render_state.json'), add)
    return len(missing)


def write_progress(status, phase, extra=None):
    rf = os.path.join(SCR, 'results.jsonl')
    n_res = sum(1 for _ in open(rf)) if os.path.exists(rf) else 0
    n_builds = len([d for d in os.listdir(os.path.join(SCR, 'builds'))
                    if os.path.exists(os.path.join(SCR, 'builds', d, '.done'))]) \
        if os.path.exists(os.path.join(SCR, 'builds')) else 0
    gdir = os.path.join(OUT, 'geometry')
    gsize = 0
    if os.path.isdir(gdir):
        for dp, dn, fn in os.walk(gdir):
            for f in fn:
                gsize += os.path.getsize(os.path.join(dp, f))
    started = float(open(os.path.join(SCR, 'start_time')).read())
    elapsed_h = round((time.time() - started) / 3600, 2)
    files_written = sum(1 for dp, dn, fn in os.walk(OUT) for f in fn) if os.path.isdir(OUT) else 0
    body = """# PROGRESS.md — Assignment 16 (rendered-geometry-history)

- status: %s
- phase: %s
- elapsed_hours: %.2f
- files_written: %d
- last_check_in: %s
- builds_done: %d / 102
- render_results: %d
- geometry_size_mb: %.1f
- blockers: %s
""" % (status, phase, elapsed_h, files_written,
       datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
       n_builds, n_res, gsize / 1048576, (extra or 'none'))
    for p in [os.path.join(BASE, 'PROGRESS.md'),
              os.path.join(REPO, '16-rendered-geometry-history', 'PROGRESS.md')]:
        with open(p, 'w') as fh:
            fh.write(body)
    return body


def main():
    resume = '--resume' in sys.argv
    if resume:
        log('RESUME mode: keeping existing state files')
        shas = json.load(open(os.path.join(SCR, 'build_state.json')))['commits']
        if not os.path.exists(os.path.join(SCR, 'start_time')):
            open(os.path.join(SCR, 'start_time'), 'w').write(str(time.time()))

        # build recovery: rewind next pointer past any claimed-but-unfinished builds
        def rewind(st):
            n = st['next']
            for i in range(n):
                sha12 = st['commits'][i][:12]
                bdir = os.path.join(SCR, 'builds', sha12)
                if not (os.path.exists(os.path.join(bdir, '.done')) or
                        os.path.exists(os.path.join(bdir, '.failed'))):
                    log('build recovery: rewinding next %d -> %d' % (n, i))
                    st['next'] = i
                    break
            return st
        locked_json(os.path.join(SCR, 'build_state.json'), rewind)
        write_progress('in_progress', 'resume')
        spawn([sys.executable, os.path.join(BASE, 'scripts', 'pusher.py'), '--reconcile'], 'pusher')
        for i in range(1, N_BUILD):
            spawn([sys.executable, os.path.join(BASE, 'scripts', 'build_worker.py'), 'b%d' % i],
                  'build_b%d' % i)
        rst = json.load(open(os.path.join(SCR, 'render_state.json')))
        n1 = sum(1 for j in rst['jobs'] if j['sha12'] == shas[0][:12])
        log('resume: %d commit-1 jobs expected' % n1)
        for i in range(N_RENDER):
            spawn([VENV_PY, os.path.join(BASE, 'scripts', 'render_worker.py'), 'r%d' % i],
                  'render_r%d' % i)
    else:
        open(os.path.join(SCR, 'start_time'), 'w').write(str(time.time()))
        shas = init_state()
        log('initialized; commit1=%s' % shas[0][:12])
        write_progress('in_progress', '0 (environment) / 1 (page sets)')
        spawn([sys.executable, os.path.join(BASE, 'scripts', 'pusher.py')], 'pusher')

        # build commit 1 synchronously first (fast), so renders can start
        bw = spawn([sys.executable, os.path.join(BASE, 'scripts', 'build_worker.py'), 'b0'], 'build_b0')
        while not os.path.exists(os.path.join(SCR, 'builds', shas[0][:12], '.done')):
            if os.path.exists(os.path.join(SCR, 'builds', shas[0][:12], '.failed')):
                log('FATAL: commit-1 build failed'); sys.exit(1)
            time.sleep(5)
        log('commit-1 built')
        bw.terminate()  # b0 must not claim commit 2; parallel workers take it from here
        try:
            bw.wait(timeout=30)
        except Exception:
            bw.kill()
        # point build_state past commit 1 for the parallel build workers
        def skip1(st):
            st['next'] = 1
            return st
        locked_json(os.path.join(SCR, 'build_state.json'), skip1)
        for i in range(1, N_BUILD):
            spawn([sys.executable, os.path.join(BASE, 'scripts', 'build_worker.py'), 'b%d' % i],
                  'build_b%d' % i)

        # enqueue commit-1 jobs, start render workers
        n1 = enqueue_commit(shas[0][:12], shas[0])
        log('enqueued %d commit-1 jobs' % n1)
        for i in range(N_RENDER):
            spawn([VENV_PY, os.path.join(BASE, 'scripts', 'render_worker.py'), 'r%d' % i],
                  'render_r%d' % i)
    commit1_12 = shas[0][:12]

    # wait for commit-1 renders to complete (supervise workers in phase A too)
    while True:
        n_ok, n_fail, b1 = results_for(commit1_12)
        if n_ok + n_fail >= n1:
            healed = heal_missing_files()
            if healed:
                rst = json.load(open(os.path.join(SCR, 'render_state.json')))
                n1 = sum(1 for j in rst['jobs'] if j['sha12'] == commit1_12)
                log('healed %d; n1 now %d' % (healed, n1))
                continue
            break
        for name, p in procs:
            if p.poll() is not None:
                if name == 'pusher':
                    if os.path.exists(os.path.join(SCR, 'PUSHER_STOP')):
                        continue
                    args = [sys.executable, os.path.join(BASE, 'scripts', 'pusher.py')]
                    if resume:
                        args.append('--reconcile')
                    spawn(args, name)
                    log('restarted dead worker pusher')
                elif name.startswith('render_'):
                    wid = name.split('_')[1]
                    spawn([VENV_PY, os.path.join(BASE, 'scripts', 'render_worker.py'), wid], name)
                    log('restarted dead render worker %s' % name)
        time.sleep(20)
    log('commit-1 renders done: ok=%d fail=%d' % (n_ok, n_fail))
    flags = decide_drops(commit1_12)
    apply_drops_to_commit1(commit1_12, flags)
    write_progress('in_progress', '2 (rendering commits 2-102)',
                   'drop flags: %s' % json.dumps(flags))


    # phase B: enqueue each build as it completes
    last_prog = time.time()
    while True:
        enq = json.load(open(os.path.join(SCR, 'enqueued.json')))
        for sha in shas[1:]:
            sha12 = sha[:12]
            if sha12 in enq:
                continue
            bdir = os.path.join(SCR, 'builds', sha12)
            if os.path.exists(os.path.join(bdir, '.done')):
                n = enqueue_commit(sha12, sha)
                log('enqueued %s (%d jobs)' % (sha12, n))
            elif os.path.exists(os.path.join(bdir, '.failed')):
                # record render-failures for all its pages (build failed)
                pages = json.load(open(os.path.join(OUT, 'pages', sha12 + '.json')))['pages']
                with open(os.path.join(SCR, 'results.jsonl'), 'a') as fh:
                    fcntl.flock(fh, fcntl.LOCK_EX)
                    for e in pages:
                        for vp in VIEWPORTS:
                            fh.write(json.dumps({'ok': False, 'sha12': sha12, 'full_sha': sha,
                                                 'page': e['page'], 'viewport': vp,
                                                 'error': 'build failed (see build log)',
                                                 'error_kind': 'environment_incomplete',
                                                 'worker': 'orchestrator'}) + '\n')
                    fcntl.flock(fh, fcntl.LOCK_UN)
                def mark(lst):
                    lst.append(sha12); return lst
                locked_json(os.path.join(SCR, 'enqueued.json'), mark, [])
                log('build failed for %s; recorded render failures' % sha12)
        # check completion: all builds terminal and queue drained
        bst = json.load(open(os.path.join(SCR, 'build_state.json')))
        builds_terminal = all(
            os.path.exists(os.path.join(SCR, 'builds', s[:12], '.done')) or
            os.path.exists(os.path.join(SCR, 'builds', s[:12], '.failed')) for s in shas)
        rst = json.load(open(os.path.join(SCR, 'render_state.json')))
        queue_empty = rst['next'] >= len(rst['jobs'])
        if builds_terminal and queue_empty and len(json.load(open(os.path.join(SCR, 'enqueued.json')))) == 102:
            # give workers a moment to finish in-flight renders
            time.sleep(60)
            rst2 = json.load(open(os.path.join(SCR, 'render_state.json')))
            if rst2['next'] >= len(rst2['jobs']):
                break
        if time.time() - last_prog > 1800:
            write_progress('in_progress', '2 (rendering)')
            last_prog = time.time()
        # restart dead workers
        for name, p in procs:
            if p.poll() is not None and (name.startswith('render_') or name == 'pusher'):
                if name == 'pusher':
                    if os.path.exists(os.path.join(SCR, 'PUSHER_STOP')):
                        continue
                    args = [sys.executable, os.path.join(BASE, 'scripts', 'pusher.py')]
                    if resume:
                        args.append('--reconcile')
                    spawn(args, name)
                else:
                    wid = name.split('_')[1]
                    spawn([VENV_PY, os.path.join(BASE, 'scripts', 'render_worker.py'), wid], name)
                log('restarted dead worker %s' % name)
        time.sleep(30)

    # heal any file losses from phase B before marking complete
    while True:
        healed = heal_missing_files()
        if not healed:
            break
        log('phase-B heal: %d re-enqueued; waiting for drain' % healed)
        for _ in range(120):  # up to 1h for heal jobs to drain
            time.sleep(30)
            rst = json.load(open(os.path.join(SCR, 'render_state.json')))
            if rst['next'] >= len(rst['jobs']):
                break

    # mark queue complete so render workers exit
    def finish(st):
        st['enqueued_all'] = True
        return st
    locked_json(os.path.join(SCR, 'render_state.json'), finish)
    log('queue complete; waiting for render workers to exit')
    for name, p in procs:
        if name.startswith('render_'):
            try:
                p.wait(timeout=600)
            except Exception:
                p.kill()
    for name, p in procs:
        if name.startswith('build_') and p.poll() is None:
            p.terminate()
    log('all workers done')
    write_progress('in_progress', '3 (deltas + summary)')

    # ---- Phase 3: deltas ----
    r = subprocess.run([sys.executable, os.path.join(BASE, 'scripts', 'phase3_deltas.py')],
                       capture_output=True, text=True, timeout=7200)
    log('phase3 stdout tail: %s' % r.stdout[-500:])
    log('phase3 stderr tail: %s' % r.stderr[-500:])
    if r.returncode != 0:
        log('FATAL: phase3 failed'); sys.exit(1)

    # ---- summary (recomputed from files) ----
    r = subprocess.run([sys.executable, os.path.join(BASE, 'scripts', 'recompute_summary.py')],
                       capture_output=True, text=True, timeout=3600)
    log('summary stdout tail: %s' % r.stdout[-800:])
    log('summary stderr tail: %s' % r.stderr[-500:])
    if r.returncode != 0:
        log('FATAL: summary recompute failed'); sys.exit(1)
    write_progress('complete', 'done')

    # ---- wait for the pusher to drain, then stop it ----
    log('waiting for pusher to drain')
    for _ in range(240):  # up to 4h
        time.sleep(60)
        st = json.load(open(os.path.join(SCR, 'push_state.json'))) \
            if os.path.exists(os.path.join(SCR, 'push_state.json')) else {}
        pushed = st.get('pushed', {})
        # verify every output file (settled) is tracked and current
        pending = 0
        for dp, dn, fn in os.walk(OUT):
            for f in fn:
                full = os.path.join(dp, f)
                rel = os.path.relpath(full, REPO)
                stt = os.stat(full)
                ent = pushed.get(rel)
                if not ent or ent['size'] != stt.st_size:
                    pending += 1
        pf = os.path.join(BASE, 'PROGRESS.md')
        rel = os.path.relpath(pf, REPO)
        stt = os.stat(pf)
        ent = pushed.get(rel)
        if not ent or ent['size'] != stt.st_size:
            pending += 1
        if pending == 0:
            break
        log('pusher drain: %d files pending' % pending)
    open(os.path.join(SCR, 'PUSHER_STOP'), 'w').write('stop')
    for name, p in procs:
        if name == 'pusher':
            try:
                p.wait(timeout=900)
            except Exception:
                p.kill()
    final_sha = subprocess.run(['git', 'ls-remote',
                                'https://github.com/nhunsaker/handoff-assignments-202609',
                                'refs/heads/main'],
                               capture_output=True, text=True, timeout=60).stdout.split()[0]
    log('FINAL remote main: %s' % final_sha)
    with open(os.path.join(SCR, 'final_sha.txt'), 'w') as fh:
        fh.write(final_sha + '\n')
    write_progress('complete', 'done')


if __name__ == '__main__':
    main()
