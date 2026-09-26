#!/usr/bin/env python3
"""Render worker (run with the venv python that has playwright).

Usage: render_worker.py <worker_id>
Holds one Chromium; claims jobs from scratch/render_state.json (flock);
fresh browser context per render; writes output/geometry/<sha12>/<viewport>/<page__>.json.gz;
appends result rows to scratch/results.jsonl (flock).
"""
import sys, os, re, json, gzip, time, hashlib, fcntl, datetime
from playwright.sync_api import sync_playwright

WID = sys.argv[1]
BASE = os.path.expanduser('~/workspace/handoff-assignments-202609/16-rendered-geometry-history')
SCR = os.path.join(BASE, 'scratch')
OUT = os.path.join(BASE, 'output')
CHROME = '/opt/meta-chromium/chrome'
VIEWPORTS = ['1280x800', '390x844']

COLLECT_JS = r"""
() => {
  const out = [];
  const els = document.body.getElementsByTagName('*');
  for (let i = 0; i < els.length; i++) {
    const el = els[i];
    const parts = [];
    let node = el;
    while (node) {
      const tag = node.tagName.toLowerCase();
      if (tag === 'html' || tag === 'body') { parts.unshift(tag); }
      else {
        let n = 1, sib = node.previousElementSibling;
        while (sib) { if (sib.tagName.toLowerCase() === tag) n++; sib = sib.previousElementSibling; }
        parts.unshift(tag + ':nth-of-type(' + n + ')');
      }
      node = node.parentElement;
    }
    const cs = getComputedStyle(el);
    const attrs = {};
    for (const a of el.attributes) {
      const nm = a.name.toLowerCase();
      if (nm === 'class' || nm === 'id' || nm === 'style') continue;
      attrs[a.name] = a.value.slice(0, 200);
    }
    const r = el.getBoundingClientRect();
    out.push({
      path: parts.join(' > '), tag: el.tagName.toLowerCase(),
      id: el.id || null, class: el.getAttribute('class'), attrs: attrs,
      _text: el.textContent, text_len: el.textContent.length,
      child_count: el.children.length,
      x: r.x, y: r.y, w: r.width, h: r.height,
      display: cs.display, position: cs.position,
    });
  }
  return out;
}
"""

FONTS_JS = r"""
(async () => {
  const fam = getComputedStyle(document.body).fontFamily;
  try { await Promise.race([document.fonts.ready, new Promise(r => setTimeout(r, 8000))]); } catch (e) {}
  let check = false;
  try { check = document.fonts.check('16px ' + fam); } catch (e) {}
  return {body_font_family: fam, fonts_ready_resolved: true, fonts_check: check};
})()
"""


def rewrite(html, root):
    def sub_attr(m):
        attr, q, val = m.group(1), m.group(2), m.group(3)
        if val.startswith('/') and not val.startswith('//'):
            return attr + '=' + q + 'file://' + root + val + q
        return m.group(0)
    html = re.sub(r'''(href|src|poster|cite|data-src|action)=(")(/[^"]*)"''', sub_attr, html)
    html = re.sub(r"""(href|src|poster|cite|data-src|action)=(')(/[^']*)'""", sub_attr, html)

    def sub_srcset(m):
        q, val = m.group(1), m.group(2)
        parts = []
        for entry in val.split(','):
            entry = entry.strip()
            mm = re.match(r'^(/\S*)(\s+\S+)?$', entry)
            if mm and not mm.group(1).startswith('//'):
                entry = 'file://' + root + mm.group(1) + (mm.group(2) or '')
            parts.append(entry)
        return 'srcset=' + q + ', '.join(parts) + q
    html = re.sub(r'''srcset=(")([^"]*)(")''', sub_srcset, html)
    html = re.sub(r"""srcset=(')([^']*)(')""", sub_srcset, html)

    def sub_css_url(m):
        q, val = m.group(1), m.group(2)
        if val.startswith('/') and not val.startswith('//'):
            return 'url(' + q + 'file://' + root + val + q + ')'
        return m.group(0)
    html = re.sub(r'''url\((["']?)(/[^)"']*)\1\)''', sub_css_url, html)
    return html


def claim_job():
    stf = os.path.join(SCR, 'render_state.json')
    with open(stf, 'r+') as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        st = json.load(fh)
        job = None
        if st['next'] < len(st['jobs']):
            job = st['jobs'][st['next']]
            st['next'] += 1
            fh.seek(0); json.dump(st, fh); fh.truncate()
        done = st.get('enqueued_all', False)
        fcntl.flock(fh, fcntl.LOCK_UN)
        return job, done


def append_result(row):
    rf = os.path.join(SCR, 'results.jsonl')
    with open(rf, 'a') as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        fh.write(json.dumps(row) + '\n')
        fcntl.flock(fh, fcntl.LOCK_UN)


def render_one(pool, job):
    sha12, full_sha, page, viewport = job['sha12'], job['full_sha'], job['page'], job['viewport']
    w, h = [int(x) for x in viewport.split('x')]
    dist = os.path.abspath(os.path.join(SCR, 'builds', sha12, 'dist'))
    src = os.path.join(dist, page)
    if not os.path.exists(src):
        return {'ok': False, 'error': 'page %s not present in build output' % page,
                'error_kind': 'genuine'}
    with open(src, 'r', encoding='utf-8', errors='replace') as fh:
        html = fh.read()
    tmpdir = os.path.join(SCR, 'render_tmp')
    os.makedirs(tmpdir, exist_ok=True)
    tmp_html = os.path.join(tmpdir, 'w%s_%s_%s_%s.html' % (WID, sha12, viewport, page.replace('/', '__')))
    with open(tmp_html, 'w', encoding='utf-8') as fh:
        fh.write(rewrite(html, dist))

    last_err = None
    for attempt in (1, 2, 3):
        ctx = None
        try:
            browser = pool.get()
            t0 = time.time()
            ctx = browser.new_context(viewport={'width': w, 'height': h}, device_scale_factor=1)
            pg = ctx.new_page()
            pg.goto('file://' + tmp_html, wait_until='load', timeout=30000)
            pg.wait_for_timeout(2000)
            elements = pg.evaluate(COLLECT_JS)
            fonts = pg.evaluate(FONTS_JS)
            doc_height = pg.evaluate('() => document.documentElement.scrollHeight')
            load_seconds = round(time.time() - t0, 3)
            for e in elements:
                t = e.pop('_text')
                e['text_sha'] = hashlib.sha256(t.encode('utf-8')).hexdigest()
                e2 = {'path': e['path'], 'tag': e['tag'], 'id': e['id'], 'class': e['class'],
                      'attrs': e['attrs'], 'text_sha': e['text_sha'], 'text_len': e['text_len'],
                      'child_count': e['child_count'], 'x': e['x'], 'y': e['y'], 'w': e['w'],
                      'h': e['h'], 'display': e['display'], 'position': e['position']}
                e.clear(); e.update(e2)
            rec = {
                'commit': full_sha, 'sha12': sha12, 'page': page, 'viewport': viewport,
                'doc_height': doc_height, 'element_count': len(elements),
                'fonts_ready_resolved': fonts['fonts_ready_resolved'],
                'body_font_family': fonts['body_font_family'],
                'fonts_check': fonts['fonts_check'],
                'load_seconds': load_seconds, 'chromium': browser.version,
                'rendered_at_utc': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                'elements': elements,
            }
            out = os.path.join(OUT, 'geometry', sha12, viewport, page.replace('/', '__') + '.json.gz')
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with gzip.open(out, 'wb', compresslevel=6) as fh:
                fh.write(json.dumps(rec, separators=(',', ':')).encode('utf-8'))
            return {'ok': True, 'elements': len(elements), 'bytes': os.path.getsize(out),
                    'seconds': load_seconds, 'fonts_check': fonts['fonts_check']}
        except Exception as e:
            last_err = repr(e)[:600]
            if 'TargetClosedError' in last_err or 'has been closed' in last_err:
                pool.invalidate()  # browser is dead; force relaunch before retry
                time.sleep(3)
            else:
                time.sleep(5)
        finally:
            if ctx is not None:
                try: ctx.close()
                except Exception: pass
    kind = 'environment_incomplete' if any(k in (last_err or '') for k in
        ['Timeout', 'timeout', 'Target crashed', 'crashed', 'Protocol', 'TargetClosed']) else 'genuine'
    return {'ok': False, 'error': last_err, 'error_kind': kind}


class BrowserPool:
    """Holds one Chromium; relaunches when dead or every MAX_RENDERS renders."""

    MAX_RENDERS = 150

    def __init__(self, playwright):
        self.p = playwright
        self.browser = None
        self.n = 0

    def _launch(self):
        b = self.p.chromium.launch(executable_path=CHROME,
                                   args=['--no-sandbox', '--disable-dev-shm-usage'])
        print('worker %s: chromium %s (re)launched' % (WID, b.version), flush=True)
        return b

    def get(self):
        if self.browser is None or not self.browser.is_connected() or self.n >= self.MAX_RENDERS:
            try:
                if self.browser is not None:
                    self.browser.close()
            except Exception:
                pass
            self.browser = self._launch()
            self.n = 0
        self.n += 1
        return self.browser

    def invalidate(self):
        try:
            if self.browser is not None:
                self.browser.close()
        except Exception:
            pass
        self.browser = None
        self.n = 0

    def close(self):
        try:
            if self.browser is not None:
                self.browser.close()
        except Exception:
            pass


def main():
    idle_rounds = 0
    with sync_playwright() as p:
        pool = BrowserPool(p)
        print('worker %s: browser pool ready' % WID, flush=True)
        while True:
            job, enqueued_all = claim_job()
            if job is None:
                if enqueued_all:
                    print('worker %s: queue drained, exiting' % WID, flush=True)
                    break
                idle_rounds += 1
                if idle_rounds > 600:
                    print('worker %s: idle too long, exiting' % WID, flush=True)
                    break
                time.sleep(10)
                continue
            idle_rounds = 0
            res = render_one(pool, job)
            res.update({'sha12': job['sha12'], 'full_sha': job['full_sha'],
                        'page': job['page'], 'viewport': job['viewport'], 'worker': WID})
            append_result(res)
            if not res['ok']:
                print('worker %s FAILED %s %s %s: %s' % (WID, job['sha12'], job['page'],
                      job['viewport'], res['error'][:150]), flush=True)
        pool.close()


if __name__ == '__main__':
    main()
