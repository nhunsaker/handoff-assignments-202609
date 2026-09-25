# Assignment 21: verify the CSS layout-propagation reference by measurement, in three engines

Budget **14–18 hours**. Assignment 03 produced a structured reference of which CSS property changes move which
elements, and what stops the movement, **derived from the specifications**. Nothing in it has been measured. This
assignment turns every row of that reference into an executable test, renders it before and after the change in
Chromium, Firefox and WebKit, and records what actually moved. Where measurement disagrees with the reference, the
measurement wins and the disagreement is the finding.

## Phase 0 — Rendering environment (30 min)

The README's **Shared rendering settings** and **geometry schema** apply, in **all three engines**: Chromium,
Firefox and WebKit. If WebKit or Firefox cannot be installed, say so in `environment.json` and run the rest in the
engines you have.

## Phase 1 — Tests from the reference

Read `03-css-layout-propagation/output/`. For every row (a property, a change to it, a layout context, a claimed
set of affected elements, and any claimed stopper), write **one self-contained test**: `tests/<id>/before.html` and
`tests/<id>/after.html`, differing **only** in the one declaration under test (inline `<style>`, no external
resources, system fonts only). Each test page contains, around the changed element, at least: two previous siblings,
two following siblings, a parent, a grandparent, one descendant, and one unrelated element in a separate subtree — so
every claim about "which elements" is testable. Where the reference lists several layout contexts (block flow, flex
row, flex column, grid, absolute, float, table, inline), one test per context.

Add a test for every **stopper** the reference names (fixed height, `overflow`, `contain`, absolute positioning, grid
track sizing, `min-height`, flex `flex-shrink: 0`, …): the same change with and without the stopper present.

Target: **every row covered**; expect 150–300 tests. Number them stably and keep a `tests/index.json` mapping test id
→ reference row → context → stopper.

## Phase 2 — Measure

For each test and each engine: render `before`, render `after`, diff the geometry per element. Classify each element:
`unchanged` (all four of x, y, width, height within 0.5 px), `moved` (x or y changed), `resized` (width or height
changed), `moved_and_resized`. Group by relation to the changed element: `self`, `previous_sibling`,
`following_sibling`, `ancestor`, `descendant`, `unrelated`.

Output `results/<id>.json`: per engine, per element, before/after boxes and the class.

## Phase 3 — Compare with the reference

`agreement.json`: per test, per engine, whether the measured set of affected relations equals the reference's claim
(`agree`), is a strict subset (`reference_overclaims`), a strict superset (`reference_underclaims`), or neither
(`differs`). Where engines disagree with **each other**, say which, with both measurements. Every non-`agree` row
carries the measured numbers for the elements in question — not a description, the boxes.

## Output

```
output/
  environment.json
  tests/index.json  tests/<id>/before.html  tests/<id>/after.html
  results/<id>.json
  agreement.json
  summary.json      tests run per engine, agree / overclaims / underclaims / differs counts per engine,
                    cross-engine disagreements, reference rows with no test and why
```

## Check-ins and review

This assignment follows the repository's **check-in, self-check and review protocol** (README, "Check-ins,
self-check and review"): push `output/` at every phase boundary and at least every 2 hours with an updated
`PROGRESS.md`; before the final commit, append the return manifest and re-derive every `summary.json` number from
the returned files; after the final commit, watch for `REVIEW.md` with `status: corrections_requested` and address
every numbered item in a new commit.

## Rules
- **Never report a measurement you did not take.** Every box comes from `getBoundingClientRect()` in a real render.
- **One declaration per test.** If a test needs two changes to express a reference row, split the row and say so.
- **Environment failures are recorded per engine**, never turned into a verdict.
- **`summary.json` must be recomputable from the other files.**
- Write results as tests finish. No analysis or recommendations. Return the files.
