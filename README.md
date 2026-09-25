# handoff-assignments-202609

Self-contained research assignments for an autonomous agent. Each folder is one assignment.
Nothing here needs any file, credential, or upload from me — everything required is on the
public web or in public git repositories.

## How to take an assignment

1. Pick a folder. Read its `ASSIGNMENT.md` in full before starting.
2. Do the work. Write your output files into that folder's `output/` directory.
3. Return the files the assignment names. Nothing else.

| folder | assignment | budget |
|---|---|---|
| `01-repo-reproducibility-scan/` | Find front-end repositories whose **old commits still build today** — stratified across five stacks, two-stage funnel | 5-7 h |
| `02-toolchain-reprobe/` | Re-test 41 repositories under a **date-matched toolchain**, resolving Node and the package manager per commit instead of using one fixed version | 5-7 h |
| `03-css-layout-propagation/` | Build a structured reference of **which CSS properties move which elements**, and what stops propagation — from the specs plus web-platform-tests | 6 h |
| `04-build-manifests/` | For five surviving repositories, probe **every page-touching commit** in the densest window under a date-matched toolchain: a full manifest of what builds, in how long, producing how many pages — plus the probe harness itself | 12 h |
| `05-nav-generation-mechanics/` | For nine static-site frameworks, document and then **verify by building** how page metadata decides where a new page lands in the navigation — inclusion, ordering, tie-breaks, absent-key defaults, grouping — as an executable decision table | 12 h |
| `06-selector-stability/` | Over real consecutive commits in three repositories, measure how often five CSS-selector strategies stay on the same element, silently move to a different one, or stop resolving — with every silent-move case recorded | 8–12 h |
| `08-capturable-sites/` | Find sites that can actually be **captured**: a config-level static-output screen before any build, a 24-month recency floor on window selection, and a verdict that counts static pages in build output — with `spa` as a distinct outcome | 10–14 h |
| `07-route-enumeration/` | A verified per-framework rule for counting a site's pages in build output (ten frameworks, each checked against a second source of truth), applied to fix Assignment 04's counts, then a recent-window re-probe of the two repositories whose 04 windows were five years old | 8–12 h |
| `09-capturable-retests/` | Re-test **three repositories from 08** at the same commits: one killed by a Node 20.0.0 toolchain choice, two by network failures. The 90-second build limit is dropped | 2-4 h |
| `10-build-history-diffs/` | Build **every first-parent commit** of the three sites 08 found capturable (455 commits), hash every built page, and record per commit which pages changed and how their HTML structure changed (sibling-group insertions/removals, text-only, attribute-only), with before/after snapshots | 14-20 h |
| `11-manifests-normalized/` | Re-run the missing **per-commit manifests** for tempertemper's 102 commits with a raw, a normalized and a `<body>` hash per page, targeted insertion snapshots, and a determinism control | 2-4 h |
| `12-content-site-scan/` | **300-candidate scan for content sites with index pages** whose history builds reproducibly: static-output, index-page and build-time-network screens before any build, new-post commits in the window, and a rebuild comparison | 16-24 h |
| `13-build-determinism/` | Build three commits of twelve sites **four times each** (baseline, repeat, other timezone/locale, fresh install), classify every output difference by cause, and **test normalization rules both ways**: noise removed and real changes kept | 12-18 h |

Assignments 01-03 are independent. **04 builds on 01 and 02** — it takes their survivors and probes every commit rather than a sample. **05 is independent.** **06 and 07 both build on 04** — they use its buildable-commit lists and its toolchain ladder. 07 also uses 05's starters. Do 04 before either.

## Rules that apply to every assignment

Each `ASSIGNMENT.md` repeats the rules that matter for it, but these govern all of them.

- **Never invent anything.** Every quote, spec section, error message, or measured number must
  come from a page you actually opened or a command that actually ran. If you could not reach
  something, record that you could not reach it.
- **Verbatim means verbatim.** Where an assignment asks for exact text, copy it character for
  character. A paraphrase of normative language is useless.
- **An empty or negative result is a real answer.** "No repository qualifies", "the spec does
  not say", "the database was unreachable" are findings, often the most valuable output.
  **Do not pad a list to look productive.** A false positive costs far more than a miss,
  because it will be acted on.
- **Distinguish a broken tool from an empty result.** If a page failed to load, a site was down,
  or a rate limit was hit, say so explicitly in the log. "I searched and found nothing" and "my
  search tool failed" mean opposite things and cannot be told apart afterwards.
- **Environment failures are not subject failures.** A missing system library, a sandbox
  permission error, a registry outage — record these as environment problems, never as a failure
  of the thing being tested.
- **Report contamination.** If something goes wrong mid-run — a reboot, a deleted working
  directory, a tool that vanished — say so and re-do the affected work rather than letting the
  numbers stand.
- **No analysis, recommendations, or commentary.** Return the data files. Interpretation is not
  part of the assignment.

## Output conventions

- JSON, UTF-8, one file per part, named as the assignment specifies.
- Include the search or source log the assignment asks for, **including queries that returned
  nothing**.
- Where a field carries a literal definition, apply it literally rather than by its
  plain-English feel. The definitions are deliberately narrow.

## Scope

This repository holds only assignments appropriate to publish openly. It is not a complete list
of work in flight.
