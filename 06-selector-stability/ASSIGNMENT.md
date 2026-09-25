# Assignment 06: which element selectors survive a site's own commits?

**Phase:** P1 (see the README's phase tags)

Budget **8–12 hours**. This is a measurement study over real commit history. It needs `git`,
Node, an HTML parser from npm (`cheerio` or `jsdom`), and patience. No browser.

## The question

Visual-regression and end-to-end tooling addresses page elements with CSS selectors and then
compares the same selector across two versions of a page. That only works if the selector still
points at **the same element** after the change. When a list gains an item, a positional
selector like `ul>li:nth-of-type(36)` silently starts pointing at the *neighbour* — it still
resolves, so nothing errors, but the comparison is now between two different elements.

I want to know, from real commits on real sites, **how often each selector strategy stays on
the same element, how often it silently moves to a different one, and how often it stops
resolving at all** — and which strategy is most stable.

You may clone repositories and run builds. Nothing will be uploaded to you.

---

## Phase 0 — Environment (20 min)

Node 20/22, npm, git, and install `cheerio` (or `jsdom`) into a scratch project. Confirm you
can build the repositories below (Assignment 04 already did, using the same date-matched
toolchain ladder — reuse it). Record in `environment.json`.

---

## The commit pairs

Use the repositories Assignment 04 proved buildable, in this order:

| repo | why | pairs |
|---|---|---|
| `midudev/jsconf.es` | 146 buildable commits in one window, 84 consecutive | up to 145 consecutive pairs |
| `11ty/eleventy-base-blog` | small, clean, no framework | the 5 buildable |
| `mrsibe/KnowNote` | 41 buildable commits, a real app | the buildable consecutive pairs |

A **pair** is two consecutive *buildable* commits in that repo's window (skip a broken commit
and pair across it, but record that you did). For each pair, build both sides and keep the
HTML output of every route that exists on both sides. If a repo yields more than **100 pairs**,
take the 100 most recent and say so.

---

## Phase 1 — Compute selectors on the BEFORE side (per pair)

For every element in every page on the BEFORE side, compute all five selectors:

| strategy | definition |
|---|---|
| **`positional`** | tag path from `body`, joined by `>`. A step is the bare tag if the element is the **only child of that tag** among its siblings, else `tag:nth-of-type(k)`. Example: `body>div:nth-of-type(2)>nav>ul:nth-of-type(3)>li:nth-of-type(4)>a` |
| **`id-anchored`** | `#<id>` of the nearest ancestor-or-self with an `id`, then the positional path from there. No id anywhere → same as positional |
| **`class-anchored`** | tag plus **all** class names at each step (`div.foo.bar>ul.nav>li>a.link`), positional index only when classes do not disambiguate |
| **`attribute-anchored`** | nearest ancestor-or-self with a `data-*`, `aria-label`, `name`, or `href` attribute, as `tag[attr="value"]`, then positional from there |
| **`text-anchored`** | for elements with direct text: `tag` + normalised text (`a{"Question pages"}`) — unique within the page or discarded |

Record, per element, its **content fingerprint**: tag, normalised direct text, `href` if any,
and `id` if any. That fingerprint is how you tell "same element" from "different element."

---

## Phase 2 — Resolve on the AFTER side and classify (per pair)

For each BEFORE element and each strategy, apply the selector to the AFTER page:

| outcome | meaning |
|---|---|
| **`stable`** | resolves to exactly one element whose fingerprint **matches** |
| **`aliased`** | resolves to exactly one element whose fingerprint **differs** — silent failure |
| **`ambiguous`** | resolves to more than one element |
| **`vanished`** | resolves to nothing |

`aliased` is the outcome I care about most. It is the one that produces a wrong answer with no
error. Record every aliased case with both fingerprints so I can see what it pointed at instead.

Also record, per pair, what kind of change it was: number of elements added/removed, whether
any `<ul>`/`<ol>` gained or lost children, whether the page's element count changed.

---

## Phase 3 — Aggregate (per repo, then overall)

`output/<repo>/stability.json`:

```json
{
  "repo": "", "pairs": 0, "elements_scored": 0,
  "by_strategy": {
    "positional": {"stable": 0.0, "aliased": 0.0, "ambiguous": 0.0, "vanished": 0.0},
    "id-anchored": {}, "class-anchored": {}, "attribute-anchored": {}, "text-anchored": {}
  },
  "aliased_by_change_kind": {
    "list_gained_child": {"positional": 0.0, "class-anchored": 0.0},
    "list_lost_child": {},
    "no_list_change": {}
  },
  "worst_pairs": [{"before": "sha", "after": "sha", "positional_aliased_rate": 0.0, "what_changed": ""}]
}
```

`output/summary.json`: the same table pooled across repos, **weighted by pair not by element**
(one page with 800 elements must not outvote ten pages with 40), plus a one-line answer per
strategy: median stable rate across pairs, and the rate on `list_gained_child` pairs
specifically — because that is where positional selectors are expected to fail and the other
strategies are expected not to.

Also `output/aliased_examples.json`: up to 200 concrete aliased cases across all repos, each
with the selector, both fingerprints, the repo, the pair, and the strategy. This file is the
one a human will read.

---

## Rules

- **Fingerprint match is the only definition of "same element."** Do not decide by intuition
  that two elements are "probably the same."
- **Every rate comes from a comparison that ran.** No estimated numbers.
- **Report a strategy that does badly honestly.** If `positional` aliases on 30% of list
  changes, that is the finding. If `text-anchored` is discarded as non-unique for most elements,
  report the discard rate rather than silently dropping it.
- **Write each repo's file when that repo finishes.** Do not batch.
- No analysis or recommendations. Return the files.
