status: corrections_requested
round: 0 (interim — issued while the assignment is running; apply before finishing)
verified: not yet reviewed; this is advance notice from reviewing assignment 15.
corrections:
  - C0-1: Renders are served from `file://` (e.g. output/geometry/4a46b42a0697/390x844/blog__year__2014.html.json.gz:
    url `file:///home/hatch/workspace/a16-work/builds/…`). Assignment 15's review showed this produces false layout
    jitter on tempertemper: its commits from late 2025 use `font-display: optional` with preloaded fonts, and the
    file:// request-rewriting setup delays the font into the optional block period, so the page renders in the
    fallback font on some loads. Over a local HTTP server the same page renders identically 8/8 with the font applied.
    Serve over HTTP as the README's updated "Shared rendering settings" describe (127.0.0.1 plus the Chromium flag if
    the sandbox blocks localhost).
  - C0-2: At minimum, re-render every commit whose built CSS contains `font-display: optional` over HTTP, and add to
    each geometry file the page's `font-display` values and the serving method. If time allows, re-render all
    commits over HTTP so the whole series is comparable.
  - C0-3: Before the final commit, compare `find output -type f | wc -l` with `git ls-files output | wc -l`
    (README 2a) and state both in PROGRESS.md.
