#!/usr/bin/env python3
"""Render one (commit dist, page, viewport) and record body-element geometry.

Usage: render_one.py <dist_dir> <page_relpath> <viewport WxH> <out_gz> <sha12> <full_sha> [--tmpdir D]

Writes gzipped JSON per the assignment-16 geometry schema. Prints a one-line JSON
result to stdout: {"ok": true, "elements": N, "bytes": B, "seconds": S} or
{"ok": false, "error": "...", "error_kind": "environment_incomplete"|"genuine"}.
"""
import sys, os, re, json, gzip, time, hashlib, traceback, datetime

DIST, PAGE, VIEWPORT, OUT_GZ, SHA12, FULL_SHA = sys.argv[1:7]
TMPDIR = None
for i, a in enumerate(sys.argv):
    if a == '--tmpdir':
        TMPDIR = sys.argv[i + 1]

W, H = [int(x) for x in VIEWPORT.split('x')]
CHROME = '/opt/meta-chromium/chrome'
VENV_PY = os.path.expanduser('~/workspace/a15-work/venv/bin/python')

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
      path: parts.join(' > '),
      tag: el.tagName.toLowerCase(),
      id: el.id || null,
      class: el.getAttribute('class'),
      attrs: attrs,
      _text: el.textContent,
      text_len: el.textContent.length,
      child_count: el.children.length,
      x: r.x, y: r.y, w: r.width, h: r.height,
      display: cs.display,
      position: cs.position,
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

HEIGHT_JS = "() => document.documentElement.scrollHeight"


def rewrite(html, root):
    """Rewrite root-relative URLs to absolute file:// URLs rooted at the dist dir."""
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


def main():
    t_start = time.time()
    src = os.path.join(DIST, PAGE)
    if not os.path.exists(src):
        print(json.dumps({'ok': False, 'error': 'page %s not present in build output' % PAGE,
                          'error_kind': 'genuine'}))
        return
    with open(src, 'r', encoding='utf-8', errors='replace') as fh:
        html = fh.read()
    tmpdir = TMPDIR or '/tmp/a16-render'
    os.makedirs(tmpdir, exist_ok=True)
    tmp_html = os.path.join(tmpdir, '%s_%s_%s.html' % (SHA12, VIEWPORT, PAGE.replace('/', '__')))
    with open(tmp_html, 'w', encoding='utf-8') as fh:
        fh.write(rewrite(html, DIST))
    url = 'file://' + tmp_html

    # Run playwright in a subprocess of the venv python so this script has no deps.
    runner = os.path.join(tmpdir, '_run_pw.py')
    if not os.path.exists(runner):
        with open(runner, 'w') as fh:
            fh.write(RUNNER_SRC)
    import subprocess
    payload = json.dumps({'url': url, 'w': W, 'h': H})
    try:
        r = subprocess.run([VENV_PY, runner], input=payload.encode(),
                           capture_output=True, timeout=120)
    except subprocess.TimeoutExpired:
        print(json.dumps({'ok': False, 'error': 'playwright subprocess timed out after 120s',
                          'error_kind': 'environment_incomplete'}))
        return
    if r.returncode != 0:
        err = (r.stderr.decode(errors='replace')[-1500:] or r.stdout.decode(errors='replace')[-1500:])
        kind = 'environment_incomplete' if any(k in err for k in
            ['Timeout', 'timeout', 'Target crashed', 'crashed', 'ECONNREFUSED', 'browser']) else 'genuine'
        print(json.dumps({'ok': False, 'error': 'playwright failed: ' + err.strip().splitlines()[-1][:500] if err.strip() else 'playwright failed with no output',
                          'error_kind': kind}))
        return
    data = json.loads(r.stdout.decode())
    if not data.get('ok'):
        err = data.get('error', 'unknown')
        kind = 'environment_incomplete' if any(k in err for k in
            ['Timeout', 'timeout', 'Target crashed', 'crashed']) else 'genuine'
        print(json.dumps({'ok': False, 'error': err[:500], 'error_kind': kind}))
        return
    load_seconds = round(time.time() - t_start, 3)
    elements = data['elements']
    for e in elements:
        t = e.pop('_text')
        e['text_sha'] = hashlib.sha256(t.encode('utf-8')).hexdigest()
        # reorder keys to spec order
        e2 = {'path': e['path'], 'tag': e['tag'], 'id': e['id'], 'class': e['class'],
              'attrs': e['attrs'], 'text_sha': e['text_sha'], 'text_len': e['text_len'],
              'child_count': e['child_count'], 'x': e['x'], 'y': e['y'], 'w': e['w'],
              'h': e['h'], 'display': e['display'], 'position': e['position']}
        e.clear(); e.update(e2)
    rec = {
        'commit': FULL_SHA, 'sha12': SHA12, 'page': PAGE, 'viewport': VIEWPORT,
        'doc_height': data['doc_height'], 'element_count': len(elements),
        'fonts_ready_resolved': data['fonts']['fonts_ready_resolved'],
        'body_font_family': data['fonts']['body_font_family'],
        'fonts_check': data['fonts']['fonts_check'],
        'load_seconds': load_seconds,
        'chromium': data['chromium'],
        'rendered_at_utc': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'elements': elements,
    }
    os.makedirs(os.path.dirname(OUT_GZ), exist_ok=True)
    raw = json.dumps(rec, separators=(',', ':')).encode('utf-8')
    with gzip.open(OUT_GZ, 'wb', compresslevel=6) as fh:
        fh.write(raw)
    print(json.dumps({'ok': True, 'elements': len(elements),
                      'bytes': os.path.getsize(OUT_GZ), 'seconds': load_seconds}))


RUNNER_SRC = '''
import json, sys
from playwright.sync_api import sync_playwright

COLLECT_JS = %r
FONTS_JS = %r
HEIGHT_JS = %r

def main():
    job = json.loads(sys.stdin.read())
    out = {}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=%r,
                args=['--no-sandbox', '--disable-dev-shm-usage'])
            ctx = browser.new_context(viewport={'width': job['w'], 'height': job['h']},
                                      device_scale_factor=1)
            page = ctx.new_page()
            page.goto(job['url'], wait_until='load', timeout=30000)
            page.wait_for_timeout(2000)
            out['elements'] = page.evaluate(COLLECT_JS)
            out['fonts'] = page.evaluate(FONTS_JS)
            out['doc_height'] = page.evaluate(HEIGHT_JS)
            out['chromium'] = browser.version
            ctx.close(); browser.close()
            out['ok'] = True
    except Exception as e:
        out = {'ok': False, 'error': repr(e)[:800]}
    sys.stdout.write(json.dumps(out))

main()
''' % (COLLECT_JS, FONTS_JS, HEIGHT_JS, CHROME)

if __name__ == '__main__':
    main()
