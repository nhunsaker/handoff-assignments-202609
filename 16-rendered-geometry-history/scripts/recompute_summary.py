#!/usr/bin/env python3
"""Recompute output/summary.json from the other output files (self-check).

Derives every number from output/pages/, output/geometry/, output/deltas/.
Failed renders are reconstructed structurally (page in page set + no geometry
file for a planned viewport); error strings/kinds come from scratch/results.jsonl
(the ground-truth worker log) and are verified against that structure.
Exits nonzero if any check fails.
"""
import os, json, gzip, re, sys, glob, statistics, datetime, fcntl

BASE = os.path.expanduser('~/workspace/handoff-assignments-202609/16-rendered-geometry-history')
OUT = os.path.join(BASE, 'output')
SCR = os.path.join(BASE, 'scratch')
REPO = os.path.expanduser('~/workspace/handoff-assignments-202609')
LIST_RE = re.compile(r'^(index\.html|blog/index\.html|blog/year/[^/]+\.html|category/[^/]+\.html)$')
VIEWPORTS = ['1280x800', '390x844']
errors = []


def check(cond, msg):
    if not cond:
        errors.append(msg)


def main():
    commits = json.load(open(os.path.join(REPO, '10-build-history-diffs', 'output', 'commits',
                                          'tempertemper__www.tempertemper.net.json')))
    shas = [c['sha'] for c in commits]
    check(len(shas) == 102, 'expected 102 commits, got %d' % len(shas))

    flags = json.load(open(os.path.join(SCR, 'flags.json')))
    # planned viewports per page given flags
    def planned_vps(page):
        if flags['drop_390_nonlist'] and not LIST_RE.match(page):
            return ['1280x800']
        return VIEWPORTS

    # worker log for error strings
    log_rows = []
    rf = os.path.join(SCR, 'results.jsonl')
    if os.path.exists(rf):
        with open(rf) as fh:
            for line in fh:
                try:
                    log_rows.append(json.loads(line))
                except Exception:
                    pass
    log_by_job = {}
    for r in log_rows:
        log_by_job[(r['sha12'], r['page'], r['viewport'])] = r

    per_commit = []
    total_elements = 0
    font_ok = 0
    geo_files = 0
    geo_bytes = 0
    failed = []
    for idx, sha in enumerate(shas):
        sha12 = sha[:12]
        pset = json.load(open(os.path.join(OUT, 'pages', sha12 + '.json')))
        check(pset['sha'] == sha, 'pages file sha mismatch %s' % sha12)
        check(pset['commit_index'] == idx, 'pages file index mismatch %s' % sha12)
        n_files = 0
        n_fail = 0
        for e in pset['pages']:
            for vp in planned_vps(e['page']):
                f = os.path.join(OUT, 'geometry', sha12, vp, e['page'].replace('/', '__') + '.json.gz')
                if os.path.exists(f):
                    n_files += 1
                    geo_files += 1
                    geo_bytes += os.path.getsize(f)
                    rec = json.loads(gzip.open(f, 'rb').read())
                    check(rec['commit'] == sha, 'geometry commit mismatch %s %s' % (sha12, e['page']))
                    check(rec['page'] == e['page'], 'geometry page mismatch %s' % sha12)
                    check(rec['viewport'] == vp, 'geometry viewport mismatch %s' % sha12)
                    check(rec['element_count'] == len(rec['elements']),
                          'element_count mismatch %s %s %s' % (sha12, e['page'], vp))
                    total_elements += rec['element_count']
                    if rec.get('fonts_check'):
                        font_ok += 1
                    # schema check on first element
                    if rec['elements']:
                        el = rec['elements'][0]
                        for k in ('path', 'tag', 'id', 'class', 'attrs', 'text_sha', 'text_len',
                                  'child_count', 'x', 'y', 'w', 'h', 'display', 'position'):
                            check(k in el, 'element missing key %s (%s %s %s)' % (k, sha12, e['page'], vp))
                            break
                else:
                    n_fail += 1
                    row = log_by_job.get((sha12, e['page'], vp))
                    check(row is not None and not row.get('ok'),
                          'missing geometry with no failure log row: %s %s %s' % (sha12, e['page'], vp))
                    failed.append({'sha12': sha12, 'full_sha': sha, 'page': e['page'], 'viewport': vp,
                                   'error': (row.get('error', '') if row else ''),
                                   'error_kind': (row.get('error_kind', '') if row else '')})
        # every failure-log row for this commit must correspond to a missing file
        for (s12, pg, vp), row in log_by_job.items():
            if s12 == sha12 and not row.get('ok'):
                f = os.path.join(OUT, 'geometry', s12, vp, pg.replace('/', '__') + '.json.gz')
                check(not os.path.exists(f), 'failure row but geometry exists: %s %s %s' % (s12, pg, vp))
        per_commit.append({'sha12': sha12, 'full_sha': sha, 'commit_index': idx,
                           'pages_in_set': len(pset['pages']),
                           'geometry_files': n_files, 'renders_failed': n_fail})

    # deltas
    delta_files = glob.glob(os.path.join(OUT, 'deltas', '*', '*.json'))
    delta_pairs = sorted(set(os.path.basename(os.path.dirname(f)) for f in delta_files))
    check(len(delta_pairs) == 101, 'expected 101 delta pairs, got %d' % len(delta_pairs))

    files_per_commit = [c['geometry_files'] for c in per_commit]
    built = [c for c in per_commit if c['geometry_files'] > 0 or c['renders_failed'] > 0]
    summary = {
        'assignment': '16-rendered-geometry-history',
        'commits_total': 102,
        'commits_with_geometry': sum(1 for c in per_commit if c['geometry_files'] > 0),
        'geometry_files_per_commit': {
            'min': min(files_per_commit), 'median': statistics.median(files_per_commit),
            'max': max(files_per_commit)},
        'total_elements_recorded': total_elements,
        'geometry_file_count': geo_files,
        'geometry_size_bytes': geo_bytes,
        'failed_renders': failed,
        'failed_render_count': len(failed),
        'environment_incomplete': [f for f in failed if f['error_kind'] == 'environment_incomplete'],
        'font_loaded_rate': round(font_ok / geo_files, 4) if geo_files else 0.0,
        'font_loaded_numerators': {'fonts_check_true': font_ok, 'renders': geo_files},
        'delta_pairs': len(delta_pairs),
        'delta_files': len(delta_files),
        'dropped': {
            'attrs': flags['drop_attrs'],
            'viewport_390_nonlist_pages': flags['drop_390_nonlist'],
            'detail': ('attrs dropped from all geometry records' if flags['drop_attrs'] else 'nothing dropped')
                      + ('; 390x844 renders dropped for non-list pages' if flags['drop_390_nonlist'] else ''),
            'projection': {k: v for k, v in flags.items() if k.startswith('projected')},
        },
        'per_commit': per_commit,
        'recompute': {'script': 'scripts/recompute_summary.py',
                      'verified_at_utc': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                      'checks': 'all geometry files re-read; every number re-derived; '
                                'failed renders cross-checked against page sets and missing files'},
    }
    with open(os.path.join(OUT, 'summary.json'), 'w') as fh:
        json.dump(summary, fh, indent=1)
    print('summary written: commits_with_geometry=%d files=%d elements=%d failed=%d size=%.1fMB font_rate=%.3f' % (
        summary['commits_with_geometry'], geo_files, total_elements, len(failed),
        geo_bytes / 1048576, summary['font_loaded_rate']))
    if errors:
        print('CHECKS FAILED (%d):' % len(errors))
        for e in errors[:20]:
            print('  -', e)
        sys.exit(1)
    print('all recompute checks passed')


if __name__ == '__main__':
    main()
