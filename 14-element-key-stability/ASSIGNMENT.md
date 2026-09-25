# Assignment 14: which element keys survive a list insertion — measured over 300 real events

Budget **12–16 hours**. An element in a page can be named many ways: by its position (`li:nth-of-type(7)`), by its
`id`, by its classes, by its text, by its attributes, by its ancestors. When a new item is inserted into a list,
every positional name below it points at a different element. Assignment 10 found thousands of such insertions in
real history. This assignment measures, over 300 of them, which naming schemes keep pointing at the same element
and which silently move.

## Phase 0 — Events and pages

From `10-build-history-diffs/output/structure/*.json`, select **300 sibling-group events** of kind `insert` or
`remove`: 150 from tempertemper, 100 from alexcarpenter, 50 from efcl (fewer if a site has fewer; then take more
from the others), preferring events on distinct (pair, page) combinations and spreading over the window. For each,
rebuild both commits (toolchain from 10's probe files) and keep the before/after HTML of that page. Save them:
`pages/<site>/<from12>__<to12>/<page>.before.html` and `.after.html`.

## Phase 1 — Keys

For every element under `<body>` in both versions, compute these keys (each a string; document your exact
normalization in `keys.json`):

| key | definition |
|---|---|
| K1 | nth-of-type CSS path from `html` |
| K2 | `id` attribute, or absent |
| K3 | tag + sorted class list |
| K4 | tag + sha256 of whitespace-collapsed own text (direct text nodes only) |
| K5 | tag + sha256 of whitespace-collapsed **full** text content |
| K6 | K4 of the element + K4 of its parent + K4 of its grandparent |
| K7 | tag + sha256 of all attributes except `class`, `id`, `style` (name=value, sorted) |
| K8 | K5 + the index of this element among siblings that share its K5 (disambiguated content key) |
| K9 | K1 with every `nth-of-type` index removed (the tag chain only) |

## Phase 2 — Ground truth for "same element"

An element in `before` and an element in `after` are **the same element** when their normalized `outerHTML`
(whitespace collapsed, attributes sorted) is identical **and** that `outerHTML` occurs exactly once in each version.
Elements that fail the uniqueness condition, or whose markup changed, are `undetermined` and are excluded from the
stability rates (count them). This gives a ground truth that does not depend on any of the keys.

## Phase 3 — Measure

Per event, per key:

- **uniqueness**: fraction of elements in `before` whose key is unique within the page;
- **stability**: of the same-element pairs, the fraction whose key is identical in both versions;
- **false match**: of the same-element pairs, the fraction whose `before` key equals the key of a **different**
  element in `after` (the key points somewhere else);
- **coverage**: fraction of elements that have the key at all (K2 is absent on most).

Split every rate by relation to the event: `inside_group_before_position` (members above the insertion point),
`inside_group_after_position` (members at or below it), `outside_group_descendant_of_container`,
`outside_group_elsewhere`. K1's stability for members below the insertion point should be near zero by construction;
report it anyway — it is the baseline.

Output `results/<site>/<from12>__<to12>__<page>.json` with every rate, and the list of false matches (element,
before key, the other element it matched) for K3, K4, K5, K7 and K8.

## Output

```
output/
  environment.json
  events.json         the 300 events chosen, with their source rows from 10
  keys.json           exact key definitions as implemented (code or pseudo-code)
  pages/…             before/after HTML for every event
  results/…
  summary.json        per site and per key: median uniqueness, stability, false-match and coverage rates, each by
                      relation to the event; total same-element pairs; undetermined counts
```

## Check-ins and review

This assignment follows the repository's **check-in, self-check and review protocol** (README, "Check-ins,
self-check and review"): push `output/` at every phase boundary and at least every 2 hours with an updated
`PROGRESS.md`; before the final commit, append the return manifest and re-derive every `summary.json` number from
the returned files; after the final commit, watch for `REVIEW.md` with `status: corrections_requested` and address
every numbered item in a new commit.

## Rules
- **Every rate from real pairs of real files.** Ground truth by the outerHTML rule above; no manual judgement.
- **Undetermined elements are counted, never dropped silently.**
- **`summary.json` must be recomputable from the other files.**
- Write results as events finish. No analysis or recommendations. Return the files.
