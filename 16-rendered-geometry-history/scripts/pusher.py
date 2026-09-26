#!/usr/bin/env python3
"""Incremental chunked pusher for assignment 16 via the GitHub Git Database API.

Runs for the whole assignment: every 60s it scans for new/changed/deleted files
under output/ (+ PROGRESS.md), uploads blobs (paced <=1.2/s to respect the
5000/hr rate limit), and creates chunked commits (<=80 files per tree POST, well
under the ~100-entry comfort limit) on top of the current remote ref.
Only files whose render completed (scratch/results.jsonl ok=true) are picked up
for geometry/; other files require mtime > 60s (settled).

State: scratch/push_state.json. Verifies every ref update with git ls-remote.
Never prints or persists the raw credential.
"""
import base64, json, os, sys, time, fcntl, subprocess, datetime
import urllib.request, urllib.error
import threading
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request, read_json_response

API = "https://api.github.com"
OWNER = "nhunsaker"
REPO = "handoff-assignments-202609"
WORKDIR = os.path.expanduser("~/workspace/handoff-assignments-202609")
FOLDER = "16-rendered-geometry-history"
BASE = os.path.join(WORKDIR, FOLDER)
OUT = os.path.join(BASE, "output")
SCR = os.path.join(BASE, "scratch")
CREDENTIAL = "custom.github"
ALLOWED = ("api.github.com",)
AUTHOR = {"name": "Chippy", "email": "chippy@hatch.local"}
CHUNK_FILES = 80
UPLOAD_WORKERS = 6
UPLOAD_PACE_S = 0.77  # aggregate upload starts <= ~1.3/s -> ~4680/hr, under the 5000/hr limit
SETTLE_S = 60

_pace_lock = threading.Lock()
_next_start = [0.0]


def paced_blob_upload(rel):
    """Upload one blob; returns (rel, blob_sha). Raises on persistent failure."""
    with _pace_lock:
        wait = _next_start[0] - time.time()
        if wait > 0:
            time.sleep(wait)
        _next_start[0] = time.time() + UPLOAD_PACE_S
    with open(os.path.join(WORKDIR, rel), 'rb') as fh:
        content = base64.b64encode(fh.read()).decode('ascii')
    blob = api('POST', '/repos/%s/%s/git/blobs' % (OWNER, REPO),
               {'content': content, 'encoding': 'base64'}, retries=8)
    return rel, blob['sha']


def log(msg):
    ts = datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%SZ')
    print('[pusher %s] %s' % (ts, msg), flush=True)


def api(method, path, payload=None, retries=5):
    url = API + path
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "chippy-github-skill"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    last = None
    for i in range(retries):
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        add_surrogate_to_request(req, CREDENTIAL, allowed_hosts=ALLOWED)
        try:
            return read_json_response(urllib.request.urlopen(req, timeout=120))
        except urllib.error.HTTPError as exc:
            try:
                body = read_json_response(exc)
            except Exception:
                body = {"raw": str(exc)[:300]}
            last = RuntimeError("GitHub API %s %s -> %s: %s" % (method, path, exc.code, body))
            if exc.code in (429, 502, 503) or (500 <= exc.code < 600):
                time.sleep(10 * (i + 1))
                continue
            raise last
        except Exception as exc:
            last = exc
            time.sleep(10 * (i + 1))
    raise last


def ls_remote():
    r = subprocess.run(['git', 'ls-remote', 'https://github.com/%s/%s' % (OWNER, REPO), 'refs/heads/main'],
                       capture_output=True, text=True, timeout=60)
    return r.stdout.split()[0]


def load_state():
    p = os.path.join(SCR, 'push_state.json')
    if os.path.exists(p):
        return json.load(open(p))
    return {'pushed': {}, 'last_remote': None, 'rounds': 0}


def save_state(st):
    with open(os.path.join(SCR, 'push_state.json'), 'w') as fh:
        json.dump(st, fh)


def completed_geometry():
    """Set of repo-relative geometry paths whose render completed ok."""
    done = set()
    rf = os.path.join(SCR, 'results.jsonl')
    if not os.path.exists(rf):
        return done
    with open(rf) as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get('ok'):
                done.add(FOLDER + '/output/geometry/%s/%s/%s.json.gz' % (
                    r['sha12'], r['viewport'], r['page'].replace('/', '__')))
    return done


def reconcile():
    """Drop push_state entries that are not actually on remote main.

    Guards against a crash between a chunk commit and the ref PATCH: state may
    claim files pushed that never landed. Fetches the remote tree once and
    removes any tracked entry whose blob SHA differs or is absent.
    """
    st = load_state()
    pushed = st.get('pushed', {})
    if not pushed:
        log('reconcile: nothing tracked')
        return
    remote_sha = ls_remote()
    tree = api('GET', '/repos/%s/%s/git/trees/%s?recursive=1' % (OWNER, REPO, remote_sha))
    if tree.get('truncated'):
        log('reconcile: remote tree truncated; skipping reconcile')
        return
    remote = {t['path']: t['sha'] for t in tree.get('tree', []) if t.get('type') == 'blob'}
    dropped = 0
    for rel, ent in list(pushed.items()):
        if remote.get(rel) != ent.get('blob'):
            pushed.pop(rel)
            dropped += 1
    save_state(st)
    log('reconcile: remote=%s, dropped %d stale tracked entries, %d remain' %
        (remote_sha[:12], dropped, len(pushed)))


def scan():
    """Return (changed_or_new_paths, deleted_paths), repo-relative."""
    geo_done = completed_geometry()
    now = time.time()
    current = {}
    # geometry: only completed renders
    gdir = os.path.join(OUT, 'geometry')
    if os.path.isdir(gdir):
        for dp, dn, fn in os.walk(gdir):
            for f in fn:
                full = os.path.join(dp, f)
                rel = os.path.relpath(full, WORKDIR)
                if rel in geo_done:
                    st = os.stat(full)
                    current[rel] = (st.st_size, st.st_mtime)
    # everything else under output/ + PROGRESS.md: settled files only
    for dp, dn, fn in os.walk(OUT):
        if 'geometry' in dp.split(os.sep):
            continue
        for f in fn:
            full = os.path.join(dp, f)
            st = os.stat(full)
            if now - st.st_mtime < SETTLE_S:
                continue
            current[os.path.relpath(full, WORKDIR)] = (st.st_size, st.st_mtime)
    for name in ['PROGRESS.md']:
        full = os.path.join(BASE, name)
        if os.path.exists(full):
            st = os.stat(full)
            if now - st.st_mtime >= SETTLE_S:
                current[os.path.relpath(full, WORKDIR)] = (st.st_size, st.st_mtime)
    st = load_state()
    pushed = st['pushed']
    changed = [p for p, (sz, mt) in current.items()
               if p not in pushed or pushed[p]['size'] != sz or pushed[p]['mtime'] != mt]
    deleted = [p for p in pushed if p not in current and not p.endswith('.json.gz')]
    # geometry deletions (drop step): only delete if we previously pushed it
    deleted += [p for p in pushed if p not in current and p.endswith('.json.gz')]
    return sorted(changed), sorted(set(deleted))


def push_round():
    st = load_state()
    changed, deleted = scan()
    if not changed and not deleted:
        return False
    log('round %d: %d changed/new, %d deleted' % (st['rounds'] + 1, len(changed), len(deleted)))
    remote_sha = ls_remote()
    ref = api('GET', '/repos/%s/%s/git/ref/heads/main' % (OWNER, REPO))
    assert ref['object']['sha'] == remote_sha, 'ref mismatch'
    base_commit = api('GET', '/repos/%s/%s/git/commits/%s' % (OWNER, REPO, remote_sha))
    base_tree = base_commit['tree']['sha']
    parent_sha = remote_sha

    ops = [('upsert', p) for p in changed] + [('delete', p) for p in deleted]
    n_chunks = (len(ops) + CHUNK_FILES - 1) // CHUNK_FILES
    for ci in range(n_chunks):
        chunk = ops[ci * CHUNK_FILES:(ci + 1) * CHUNK_FILES]
        upserts = [rel for kind, rel in chunk if kind == 'upsert']
        blob_shas = {}
        if upserts:
            with ThreadPoolExecutor(max_workers=UPLOAD_WORKERS) as ex:
                futs = {ex.submit(paced_blob_upload, rel): rel for rel in upserts}
                for fut in futs:
                    rel, sha = fut.result()  # raises on persistent failure -> whole round retries
                    blob_shas[rel] = sha
        entries = []
        for kind, rel in chunk:
            if kind == 'upsert':
                entries.append({'path': rel, 'mode': '100644', 'type': 'blob', 'sha': blob_shas[rel]})
                st['pushed'][rel] = {'blob': blob_shas[rel],
                                     'size': os.path.getsize(os.path.join(WORKDIR, rel)),
                                     'mtime': os.path.getmtime(os.path.join(WORKDIR, rel))}
            else:
                entries.append({'path': rel, 'mode': '100644', 'type': 'blob', 'sha': None})
                st['pushed'].pop(rel, None)
        tree = api('POST', '/repos/%s/%s/git/trees' % (OWNER, REPO),
                   {'base_tree': base_tree, 'tree': entries})
        msg = ('Assignment 16: rendered geometry batch %d/%d (%d files)\n\n'
               'Incremental push of output/geometry + output metadata.\n'
               'Chunked commit %d of this push round.' % (ci + 1, n_chunks, len(chunk), st['rounds'] + 1))
        commit = api('POST', '/repos/%s/%s/git/commits' % (OWNER, REPO),
                     {'message': msg, 'tree': tree['sha'], 'parents': [parent_sha],
                      'author': AUTHOR})
        parent_sha = commit['sha']
        base_tree = tree['sha']
        save_state(st)
        if (ci + 1) % 10 == 0:
            log('  chunk %d/%d -> %s' % (ci + 1, n_chunks, parent_sha[:12]))
    api('PATCH', '/repos/%s/%s/git/refs/heads/main' % (OWNER, REPO), {'sha': parent_sha})
    time.sleep(5)
    verified = ls_remote()
    assert verified == parent_sha, 'push verification failed: %s != %s' % (verified, parent_sha[:12])
    st['last_remote'] = parent_sha
    st['rounds'] += 1
    save_state(st)
    log('pushed round %d: main now at %s (%d ops in %d chunks, verified)' %
        (st['rounds'], parent_sha, len(ops), n_chunks))
    return True


def main():
    if '--reconcile' in sys.argv:
        reconcile()
    log('starting; %d upload workers, paced at %.2fs aggregate' % (UPLOAD_WORKERS, UPLOAD_PACE_S))
    idle = 0
    while True:
        try:
            did = push_round()
        except Exception as e:
            log('push round failed: %r' % e)
            did = False
        if did:
            idle = 0
        else:
            idle += 1
        # stop only when the orchestrator says everything is done and pushed
        done_flag = os.path.join(SCR, 'PUSHER_STOP')
        if os.path.exists(done_flag):
            # one final sweep, then exit
            try:
                push_round()
            except Exception as e:
                log('final round failed: %r' % e)
            st = load_state()
            log('stopping; %d files tracked, remote=%s' %
                (len(st['pushed']), st.get('last_remote')))
            return
        time.sleep(60)


if __name__ == '__main__':
    main()
