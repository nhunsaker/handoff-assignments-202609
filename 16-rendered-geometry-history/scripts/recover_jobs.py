#!/usr/bin/env python3
"""Recover jobs lost to the browser-death incident:
- claimed jobs with no result row  -> re-enqueue
- failure rows caused by dead browser (TargetClosedError) -> drop row, re-enqueue
"""
import json, os, fcntl

BASE = os.path.expanduser('~/workspace/handoff-assignments-202609/16-rendered-geometry-history')
SCR = os.path.join(BASE, 'scratch')

stf = os.path.join(SCR, 'render_state.json')
with open(stf) as fh:
    st = json.load(fh)
claimed = st['jobs'][:st['next']]

recorded = set()
bad_rows = []
rows = []
rf = os.path.join(SCR, 'results.jsonl')
with open(rf) as fh:
    for line in fh:
        r = json.loads(line)
        key = (r['sha12'], r['page'], r['viewport'])
        if not r.get('ok') and 'TargetClosedError' in r.get('error', ''):
            bad_rows.append(key)
            continue  # drop the row; job will be re-rendered
        recorded.add(key)
        rows.append(line)

missing = [j for j in claimed
           if (j['sha12'], j['page'], j['viewport']) not in recorded]
# dedupe against already-queued (unclaimed) jobs
queued = set((j['sha12'], j['page'], j['viewport']) for j in st['jobs'][st['next']:])
to_add = [j for j in missing if (j['sha12'], j['page'], j['viewport']) not in queued]

with open(rf, 'w') as fh:
    fh.writelines(rows)

def add(st):
    st['jobs'].extend(to_add)
    return st
with open(stf, 'r+') as fh:
    fcntl.flock(fh, fcntl.LOCK_EX)
    s = json.load(fh)
    s['jobs'].extend(to_add)
    fh.seek(0); json.dump(s, fh); fh.truncate()
    fcntl.flock(fh, fcntl.LOCK_UN)

print('claimed:', len(claimed), 'recorded:', len(recorded),
      'dead-browser failures dropped:', len(bad_rows),
      're-enqueued:', len(to_add))
