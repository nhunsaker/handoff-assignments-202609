#!/usr/bin/env python3
"""Supervisor for assignment 16 phase A: keeps 4 render workers (s0-s3) and the
pusher alive. When the orchestrator finishes commit-1 (phase B begins), kills the
s-workers and exits so the orchestrator's own phase-B worker restart takes over
(spawns r0-r3 from its dead Popen entries). The pusher is kept alive throughout.
"""
import os, sys, time, subprocess, signal, datetime

BASE = os.path.expanduser('~/workspace/handoff-assignments-202609/16-rendered-geometry-history')
SCR = os.path.join(BASE, 'scratch')
VENV_PY = os.path.expanduser('~/workspace/a15-work/venv/bin/python')


def log(msg):
    print('[%sZ] [supervisor] %s' % (datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S'), msg), flush=True)


def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def start_render(wid):
    logf = open(os.path.join(SCR, 'logs', 'render_%s.out' % wid), 'a')
    p = subprocess.Popen([VENV_PY, os.path.join(BASE, 'scripts', 'render_worker.py'), wid],
                         stdout=logf, stderr=subprocess.STDOUT)
    log('started render worker %s pid=%d' % (wid, p.pid))
    return p.pid


def start_pusher():
    logf = open(os.path.join(SCR, 'logs', 'pusher.out'), 'a')
    p = subprocess.Popen([sys.executable, os.path.join(BASE, 'scripts', 'pusher.py')],
                         stdout=logf, stderr=subprocess.STDOUT)
    with open(os.path.join(SCR, 'pusher.pid'), 'w') as fh:
        fh.write(str(p.pid))
    log('started pusher pid=%d' % p.pid)
    return p.pid


def phase_b_started():
    try:
        with open(os.path.join(SCR, 'logs', 'orchestrator.out')) as fh:
            tail = fh.read()[-3000:]
        return 'commit-1 renders done' in tail
    except Exception:
        return False


def main():
    workers = {}
    for i in range(4):
        wid = 's%d' % i
        workers[wid] = start_render(wid)
    pusher_pid = None
    try:
        pusher_pid = int(open(os.path.join(SCR, 'pusher.pid')).read().strip())
    except Exception:
        pass
    if not pusher_pid or not alive(pusher_pid):
        pusher_pid = start_pusher()
    else:
        log('pusher already alive pid=%d' % pusher_pid)

    while True:
        time.sleep(20)
        if phase_b_started():
            log('phase B detected; stopping s-workers, supervisor exiting')
            for wid, pid in workers.items():
                try:
                    os.kill(pid, signal.SIGTERM)
                except OSError:
                    pass
            return
        if os.path.exists(os.path.join(SCR, 'SUPERVISOR_STOP')):
            log('stop flag; exiting')
            return
        for wid, pid in list(workers.items()):
            if not alive(pid):
                log('worker %s (pid %d) dead; restarting' % (wid, pid))
                workers[wid] = start_render(wid)
        try:
            pp = int(open(os.path.join(SCR, 'pusher.pid')).read().strip())
        except Exception:
            pp = None
        if not pp or not alive(pp):
            if os.path.exists(os.path.join(SCR, 'PUSHER_STOP')):
                log('pusher stop flag set; not restarting pusher')
            else:
                pusher_pid = start_pusher()


if __name__ == '__main__':
    main()
