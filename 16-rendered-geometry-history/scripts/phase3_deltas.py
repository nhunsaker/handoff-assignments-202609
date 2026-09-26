#!/usr/bin/env python3
"""Phase 3: consecutive-pair deltas for list pages at 1280x800.

For each consecutive commit pair, for each list page (index.html, blog/index.html,
blog/year/*.html, category/*.html): match elements by (tag, text_sha, parent tag +
parent text_sha); record dx,dy,dw,dh per matched element; list unmatched per side.
Output: deltas/<from12>__<to12>/<page__>.json

If a side's geometry file is missing, write {"error": ...} instead.
If nothing moved and nothing unmatched, write the compact identical form.
"""
import os, json, gzip, re, sys
from collections import defaultdict

BASE = os.path.expanduser('~/workspace/handoff-assignments-202609/16-rendered-geometry-history')
OUT = os.path.join(BASE, 'output')
REPO = os.path.expanduser('~/workspace/handoff-assignments-202609')
LIST_RE = re.compile(r'^(index\.html|blog/index\.html|blog/year/[^/]+\.html|category/[^/]+\.html)$')
VP = '1280x800'


def load_geo(sha12, page):
    f = os.path.join(OUT, 'geometry', sha12, VP, page.replace('/', '__') + '.json.gz')
    if not os.path.exists(f):
        return None
    return json.loads(gzip.open(f, 'rb').read())


def parent_key(el, by_path):
    p = el['path']
    if ' > ' not in p:
        return ('body', '')
    pp = p.rsplit(' > ', 1)[0]
    if pp == 'html > body':
        return ('body', '')
    par = by_path.get(pp)
    if par is None:
        return ('?', '')
    return (par['tag'], par['text_sha'])


def key(el, by_path):
    pt, pts = parent_key(el, by_path)
    return (el['tag'], el['text_sha'], pt, pts)


def main():
    commits = json.load(open(os.path.join(REPO, '10-build-history-diffs', 'output', 'commits',
                                          'tempertemper__www.tempertemper.net.json')))
    shas = [c['sha'] for c in commits]
    n_files = n_ident = 0
    for i in range(len(shas) - 1):
        f12, t12 = shas[i][:12], shas[i + 1][:12]
        # list pages = union of list pages in either commit's page set
        pages = set()
        for s12 in (f12, t12):
            pf = os.path.join(OUT, 'pages', s12 + '.json')
            if os.path.exists(pf):
                for e in json.load(open(pf))['pages']:
                    if LIST_RE.match(e['page']):
                        pages.add(e['page'])
        ddir = os.path.join(OUT, 'deltas', '%s__%s' % (f12, t12))
        os.makedirs(ddir, exist_ok=True)
        for page in sorted(pages):
            outp = os.path.join(ddir, page.replace('/', '__') + '.json')
            if os.path.exists(outp):
                n_files += 1
                continue
            gf, gt = load_geo(f12, page), load_geo(t12, page)
            if gf is None or gt is None:
                rec = {'from': shas[i], 'to': shas[i + 1], 'from12': f12, 'to12': t12,
                       'page': page, 'viewport': VP,
                       'error': 'missing geometry: from=%s to=%s' % (gf is not None, gt is not None)}
            else:
                ef, et = gf['elements'], gt['elements']
                bf = {e['path']: e for e in ef}
                bt = {e['path']: e for e in et}
                mf = defaultdict(list)
                for e in ef:
                    mf[key(e, bf)].append(e)
                matched, unm_t = [], []
                used = defaultdict(int)
                for e in et:
                    k = key(e, bt)
                    lst = mf.get(k, [])
                    if used[k] < len(lst):
                        f_ = lst[used[k]]
                        used[k] += 1
                        matched.append((f_, e))
                    else:
                        unm_t.append(e)
                unm_f = []
                for k, lst in mf.items():
                    for e in lst[used[k]:]:
                        unm_f.append(e)
                moved = []
                for f_, e in matched:
                    dx = e['x'] - f_['x']; dy = e['y'] - f_['y']
                    dw = e['w'] - f_['w']; dh = e['h'] - f_['h']
                    if dx or dy or dw or dh:
                        moved.append({'path': e['path'], 'tag': e['tag'],
                                      'dx': dx, 'dy': dy, 'dw': dw, 'dh': dh})
                if not moved and not unm_f and not unm_t:
                    rec = {'from': shas[i], 'to': shas[i + 1], 'from12': f12, 'to12': t12,
                           'page': page, 'viewport': VP,
                           'match_rule': ('elements matched by (tag, text_sha, parent tag + parent '
                                          'text_sha); direct children of <body> use parent key '
                                          "('body','')"),
                           'identical': True, 'matched_count': len(matched)}
                    n_ident += 1
                else:
                    rec = {'from': shas[i], 'to': shas[i + 1], 'from12': f12, 'to12': t12,
                           'page': page, 'viewport': VP,
                           'match_rule': ('elements matched by (tag, text_sha, parent tag + parent '
                                          'text_sha); direct children of <body> use parent key '
                                          "('body','')"),
                           'identical': False,
                           'matched_count': len(matched),
                           'moved': moved,
                           'moved_count': len(moved),
                           'unmatched_from': [{'path': e['path'], 'tag': e['tag']} for e in unm_f],
                           'unmatched_to': [{'path': e['path'], 'tag': e['tag']} for e in unm_t]}
            with open(outp, 'w') as fh:
                json.dump(rec, fh, separators=(',', ':'))
            n_files += 1
        if (i + 1) % 10 == 0:
            print('pairs done: %d/101, files=%d, identical=%d' % (i + 1, n_files, n_ident), flush=True)
    print('DONE files=%d identical=%d' % (n_files, n_ident))


if __name__ == '__main__':
    main()
