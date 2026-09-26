#!/usr/bin/env python3
"""Phase 1: decide which pages to render per commit.

Commit 1: every page. Later commits: every page whose <body> hash differs from the
previous built commit (using 11-manifests-normalized/output/manifests/ body hashes),
PLUS at every commit: index.html, blog/index.html, blog/year/*.html, category/*.html.

Writes pages/<sha12>.json: {sha, commit_index, previous_built_sha, pages:[{page, reason}]}.
"""
import json, glob, os, sys, re

REPO = os.path.expanduser('~/workspace/handoff-assignments-202609')
OUT = os.path.join(REPO, '16-rendered-geometry-history', 'output')
MANIFESTS = os.path.join(REPO, '11-manifests-normalized', 'output', 'manifests')
LIST_RE = re.compile(r'^(index\.html|blog/index\.html|blog/year/[^/]+\.html|category/[^/]+\.html)$')

def main():
    commits = json.load(open(os.path.join(REPO, '10-build-history-diffs', 'output', 'commits',
                                           'tempertemper__www.tempertemper.net.json')))
    shas = [c['sha'] for c in commits]
    assert len(shas) == 102, len(shas)
    # load body hashes for every commit that has a manifest
    bodies = {}
    for sha in shas:
        f = os.path.join(MANIFESTS, sha + '.json')
        if os.path.exists(f):
            m = json.load(open(f))
            bodies[sha] = {p: v['body'] for p, v in m['pages'].items()}
    print('manifests with body hashes:', len(bodies), file=sys.stderr)

    prev = None
    for i, sha in enumerate(shas):
        cur = bodies.get(sha)
        entries = []
        if i == 0 or cur is None or prev is None:
            # commit 1 (or missing hash data): every page
            pages = sorted(cur.keys()) if cur else []
            for p in pages:
                entries.append({'page': p, 'reason': 'commit_1_all_pages' if i == 0 else 'hash_data_missing'})
        else:
            prevb = bodies[prev]
            changed = [p for p, h in cur.items() if prevb.get(p) != h]
            new = [p for p in cur if p not in prevb]
            for p in sorted(changed):
                entries.append({'page': p, 'reason': 'body_hash_changed' if p in prevb else 'page_new'})
        # plus list pages regardless
        if cur:
            for p in sorted(cur.keys()):
                if LIST_RE.match(p) and p not in {e['page'] for e in entries}:
                    entries.append({'page': p, 'reason': 'list_page_always_rendered'})
        entries.sort(key=lambda e: e['page'])
        os.makedirs(os.path.join(OUT, 'pages'), exist_ok=True)
        out = {
            'sha': sha,
            'sha12': sha[:12],
            'commit_index': i,
            'previous_built_sha': prev if i else None,
            'note': 'page set decided from 11-manifests-normalized body hashes; actual render uses this repo build output',
            'pages': entries,
        }
        with open(os.path.join(OUT, 'pages', sha[:12] + '.json'), 'w') as fh:
            json.dump(out, fh, indent=1)
        prev = sha
    print('wrote', len(shas), 'page-set files')

if __name__ == '__main__':
    main()
