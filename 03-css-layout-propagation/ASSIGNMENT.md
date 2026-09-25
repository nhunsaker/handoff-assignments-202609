# Research task: build a reference table of CSS layout propagation semantics

**Phase:** P3 (see the README's phase tags)

You are compiling a structured reference from the CSS specifications. Work entirely from public
specs on the web. Nothing will be uploaded to you and you need no files from me. Budget 6 hours.

## The question

When a CSS declaration changes, some things move and some things don't. I want that written
down precisely, from the specs, as data.

For example: changing an element's `padding-top` changes its own box and pushes its following
siblings down. Changing `position` to `absolute` takes it out of flow entirely, so its siblings
close up and its later siblings move *up*. Changing `color` moves nothing at all. Changing
`width` on a flex item may move nothing, because the flex container redistributes space.

I want every layout-affecting CSS property classified this way, plus the rules that **stop**
a change from propagating further.

You may clone git repositories. **Clone the web-platform-tests suite and use it as ground
truth** wherever spec prose is ambiguous:

```
git clone --filter=blob:none --depth 1 https://github.com/web-platform-tests/wpt
```

The directories that matter are `wpt/css/CSS2/`, `wpt/css/css-flexbox/`, `wpt/css/css-grid/`,
`wpt/css/css-position/`, `wpt/css/css-sizing/` and `wpt/css/css-display/`. These are executable
tests with stated expected results — each one is a browser-verified statement about what the
spec means. **You do not need to run them.** Read the test file and its `<title>`/assert
metadata; a test named and asserted precisely is better evidence than a paragraph of spec prose.

Five parts. Each produces one JSON file.

---

## Part 1 — Property propagation table (`part1_properties.json`)

Work through the CSS specifications and classify **every property that can affect layout
geometry**. Aim for 80 to 120 properties. Skip properties that only affect paint and never
geometry (`color`, `background-color`, `box-shadow`, `outline-color`) — but **record them in a
separate `paint_only` array**, because "this cannot move anything" is a useful fact too.

Primary sources, in order of authority:
- `https://www.w3.org/TR/CSS22/` (CSS 2.2 — visual formatting model, chapters 8-10)
- `https://drafts.csswg.org/css-display/`
- `https://drafts.csswg.org/css-box/`
- `https://drafts.csswg.org/css-sizing/`
- `https://drafts.csswg.org/css-position/`
- `https://drafts.csswg.org/css-flexbox/`
- `https://drafts.csswg.org/css-grid/`
- `https://drafts.csswg.org/css-text/` and `css-inline/` for line-box effects

MDN may be used to *find* the right spec section, but **the citation must be to the spec**.

For each property:

```json
{
  "property": "padding-top",
  "spec_url": "https://www.w3.org/TR/CSS22/box.html#padding-properties",
  "spec_section": "8.4",
  "affects_own_box_size": true,
  "affects_own_position": false,
  "affects_following_siblings": true,
  "affects_preceding_siblings": false,
  "affects_ancestor_size": true,
  "affects_descendant_positions": true,
  "removes_from_flow": false,
  "depends_on_formatting_context": false,
  "depends_on_runtime_facts": [],
  "spec_quote": "VERBATIM sentence from the spec that supports the classification",
  "notes": ""
}
```

Field definitions — apply literally:

- **`affects_following_siblings`** — in normal flow, does changing this push or pull the
  elements *after* it in document order?
- **`affects_preceding_siblings`** — can changing this move elements *before* it in document
  order? This is rare and I want to know exactly which properties can do it.
- **`affects_ancestor_size`** — can this change the size of a parent whose size depends on
  content?
- **`removes_from_flow`** — does a value of this property take the element out of normal flow
  (`position: absolute`, `position: fixed`, `display: none`, `float`)? If only *some* values do,
  list them in `notes`.
- **`depends_on_formatting_context`** — true if the answer differs between normal flow, flex,
  grid, and table. If true, Part 3 must cover it.
- **`depends_on_runtime_facts`** — an array naming any information **not present in the
  stylesheet or the markup** that is needed to predict the effect. Use these exact strings where
  they apply, and add others as needed:
  `["intrinsic-image-size", "font-metrics", "font-fallback", "available-width", "content-length", "script-computed-value", "user-preference"]`

**`depends_on_runtime_facts` is the field I care about most.** A property whose effect cannot be
determined from the CSS and the markup alone is fundamentally different from one that can, and I
need that line drawn precisely with a spec quote behind it.

---

## Part 2 — Propagation barriers (`part2_barriers.json`)

Now the opposite question: **what stops a size or position change from propagating further up
or along?**

Cover at minimum: block formatting context creation (every trigger listed in the spec), `position:
absolute` / `fixed` containing blocks, `contain` values, `overflow` values that establish a BFC,
flex and grid item sizing, `display: none` subtrees, replaced-element intrinsic sizing, fixed
`height`/`width` on an ancestor, and `aspect-ratio`.

```json
{
  "barrier": "block formatting context",
  "spec_url": "", "spec_section": "",
  "what_it_blocks": "which direction of propagation stops, precisely",
  "trigger_conditions": ["every condition the spec lists that creates one"],
  "detectable_from_stylesheet_alone": true,
  "spec_quote": "VERBATIM",
  "notes": ""
}
```

**`detectable_from_stylesheet_alone`** — could you tell this barrier exists by reading the CSS
and the markup, without running a browser? Answer from the spec text, and quote it.

---

## Part 3 — Formatting-context behaviour matrix (`part3_contexts.json`)

For each of: **normal flow (block)**, **inline / line boxes**, **flex**, **grid**, **table**,
**absolutely positioned**, and **floats** — answer the same five questions, each with a spec
citation:

```json
{
  "context": "flex",
  "spec_url": "", "spec_section": "",
  "when_a_child_grows": "what moves, precisely, per the spec",
  "when_a_child_is_removed": "",
  "when_the_container_grows": "",
  "does_child_order_determine_position": true,
  "can_a_change_move_earlier_children": true,
  "spec_quotes": {"when_a_child_grows": "VERBATIM", "can_a_change_move_earlier_children": "VERBATIM"},
  "wpt_evidence": [{"path": "css/css-flexbox/...html", "title": "verbatim <title> of the test", "assertion": "verbatim assert metadata, or null"}],
  "notes": ""
}
```

`can_a_change_move_earlier_children` is the one to be careful with. In normal block flow the
answer is no. In flex with `justify-content: center`, or in grid with auto-placement, or with
`flex-wrap`, it can be yes. **Get this right, because it is the field most likely to be wrong
from intuition — and for this field specifically, back every answer with a WPT test as well as a
spec quote** (`wpt_evidence` below). If no WPT test covers it, say so.

---

## Part 4 — Hard cases from WPT (`part4_wpt_cases.json`)

Search the cloned WPT tree for tests whose titles or assertions describe **one element's change
moving another element**. Useful greps to start from, varied as you go:

```
grep -rl "does not affect" wpt/css/CSS2/ wpt/css/css-flexbox/
grep -rl "should not move" wpt/css/
grep -rli "reflow\|relayout\|shrink-to-fit\|intrinsic" wpt/css/css-sizing/
grep -rl "out-of-flow\|out of flow" wpt/css/css-position/
```

Collect 30 to 60 tests that state a propagation fact — something moved, or pointedly did not.
For each:

```json
{
  "path": "css/css-flexbox/flex-item-contains-strut.html",
  "title": "VERBATIM <title> element text",
  "assertion": "VERBATIM content of the assert meta, or null if absent",
  "spec_link": "the href of its <link rel=help>, or null",
  "propagation_fact": "one sentence: what changed, and what did or did not move as a result",
  "direction": "own-box | following-siblings | preceding-siblings | ancestor | descendants | nothing",
  "requires_runtime_facts": false
}
```

`propagation_fact` is yours to write in one sentence; everything else must be copied verbatim
from the file. Prefer tests that state a **negative** — "does not affect", "should not move" —
because barriers are what I am least able to derive from prose.

---

## Part 5 — Source log (`searches.json`)

Every spec page and search you used:

```json
[{"part": 1, "source": "drafts.csswg.org/css-flexbox", "url": "", "query_or_section": "", "opened_successfully": true}]
```

Log pages that failed to load with `opened_successfully: false` and say what happened. I need to
tell a page you could not read from a fact that is not in the spec — those mean opposite things.

---

## Rules

- **Every classification needs a verbatim spec quote.** Copy it exactly; do not paraphrase
  normative language. If you cannot find a spec sentence supporting a classification, set the
  field to `null` and explain in `notes` — do not guess from how browsers behave.
- **Never invent a spec section number or URL.** If you read it on MDN and cannot locate the
  spec passage, say so in `notes` and cite MDN explicitly as a fallback, marked as such.
- **"The spec does not say" is a real and valuable answer.** Several of these questions are
  genuinely underspecified and left to implementations. Recording that is more useful to me than
  a confident guess, because it tells me the answer is unpredictable in principle.
- **Clone shallow and do not modify the WPT tree.** You are reading it, not contributing to it.
- Do not add analysis, recommendations, or commentary. Return the five JSON files.
