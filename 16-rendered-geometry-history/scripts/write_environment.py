#!/usr/bin/env python3
"""Write output/environment.json for assignment 16 (values measured, not asserted)."""
import json, os, subprocess, datetime

BASE = os.path.expanduser('~/workspace/handoff-assignments-202609/16-rendered-geometry-history')
OUT = os.path.join(BASE, 'output')
VENV_PY = os.path.expanduser('~/workspace/a15-work/venv/bin/python')

# chromium version from the actual binary
ver = subprocess.run([VENV_PY, '-c',
    "from playwright.sync_api import sync_playwright\n"
    "with sync_playwright() as p:\n"
    "    b=p.chromium.launch(executable_path='/opt/meta-chromium/chrome',args=['--no-sandbox','--disable-dev-shm-usage'])\n"
    "    print(b.version); b.close()"],
    capture_output=True, text=True, timeout=120)
chromium_version = ver.stdout.strip()

probes = json.load(open(os.path.expanduser(
    '~/workspace/handoff-assignments-202609/10-build-history-diffs/output/probes/tempertemper__www.tempertemper.net.json')))
toolchains = {}
for c in probes['commits']:
    key = (c['node_used'], c.get('npm_version_used'), c['build_command'])
    toolchains.setdefault('%s|%s|%s' % key, []).append(c['sha'][:12])
commits = json.load(open(os.path.expanduser(
    '~/workspace/handoff-assignments-202609/10-build-history-diffs/output/commits/tempertemper__www.tempertemper.net.json')))

env = {
    'assignment': '16-rendered-geometry-history',
    'date_generated': '2026-09-26',
    'repo': 'tempertemper/www.tempertemper.net',
    'commits': [c['sha'] for c in commits],
    'commit_count': len(commits),
    'note_on_shared_rendering_settings': (
        "The repository README contains no 'Shared rendering settings' section "
        "(verified by grep over README.md on 2026-09-26; assignment 15 recorded the same finding). "
        "The settings below are the ones actually used, recorded verbatim."),
    'rendering': {
        'browser': 'Chromium %s' % chromium_version,
        'browser_binary': '/opt/meta-chromium/chrome',
        'driver': 'Playwright (python, ~/workspace/a15-work/venv)',
        'launch_args': ['--no-sandbox', '--disable-dev-shm-usage'],
        'viewports': ['1280x800', '390x844'],
        'device_scale_factor': 1,
        'context_per_render': 'fresh browser context per render (one browser per worker process)',
        'navigation': "page.goto(url, wait_until='load', timeout=30000) then 2000ms settle",
        'serving': ("pages navigated via file:// URLs; the document request uses the on-disk HTML after "
                    "rewriting root-relative URLs (href/src/poster/cite/data-src/action, srcset entries, "
                    "CSS url(...)) to absolute file:// URLs rooted at the built site directory. "
                    "Artifacts on disk are unmodified. "
                    "Chromium 152 blocks navigation from about:blank to http://127.0.0.1 "
                    "(ERR_BLOCKED_BY_LOCAL_NETWORK_ACCESS_CHECKS), and plain file:// navigation resolves "
                    "root-relative /assets/... URLs to file:///assets/... (wrong)."),
    },
    'toolchain_per_commit': {
        'source': '10-build-history-diffs/output/probes/tempertemper__www.tempertemper.net.json',
        'distinct_toolchains': [{'node': k.split('|')[0], 'npm': k.split('|')[1],
                                 'build_command': k.split('|')[2], 'commit_count': len(v)}
                                for k, v in toolchains.items()],
    },
    'geometry_schema': {
        'per_element': {
            'path': 'CSS path from html using tag for html/body and tag:nth-of-type(n) below, joined with " > "',
            'tag': 'lowercase tag name', 'id': 'id attribute or null',
            'class': 'class attribute string or null',
            'attrs': 'every attribute except class/id/style, values truncated to 200 chars',
            'text_sha': 'sha256 hex of element textContent (utf-8)',
            'text_len': 'textContent length', 'child_count': 'element.children.length',
            'x': 'getBoundingClientRect().x', 'y': 'getBoundingClientRect().y',
            'w': 'getBoundingClientRect().width', 'h': 'getBoundingClientRect().height',
            'display': 'getComputedStyle display', 'position': 'getComputedStyle position',
        },
        'per_page': ['doc_height=document.documentElement.scrollHeight', 'element_count',
                     'fonts_ready_resolved (document.fonts.ready awaited)',
                     'body_font_family=getComputedStyle(document.body).fontFamily',
                     "fonts_check=document.fonts.check('16px '+body font family)",
                     'load_seconds (goto through settle+measure)', 'chromium', 'rendered_at_utc'],
        'scope': 'every element under document.body, in document order (document.body itself excluded)',
    },
    'delta_match_rule': ("list pages only, consecutive commit pairs, 1280x800: elements matched by "
                         "(tag, text_sha, parent tag + parent text_sha); direct children of <body> use "
                         "parent key ('body',''). Per matched element dx,dy,dw,dh (to minus from); "
                         "unmatched elements listed per side."),
    'page_set_rule': ("commit 1: every page. Later commits: pages whose <body> hash differs from the "
                      "previous built commit, using 11-manifests-normalized/output/manifests/ body hashes "
                      "(verified byte-identical to a local rebuild of commit 4f1deb1e25dc index.html), "
                      "plus index.html, blog/index.html, blog/year/*.html, category/*.html at every commit."),
}
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, 'environment.json'), 'w') as fh:
    json.dump(env, fh, indent=1)
print('wrote environment.json; chromium', chromium_version)
