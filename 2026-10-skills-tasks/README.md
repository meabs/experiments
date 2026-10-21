# Do skill packs help across many different tasks? (Codex)

Written 2026-10-21, before any measured run. Later changes go in the amendment log at the bottom.

## Why this follows skills-impact

[2026-10-skills-impact](../2026-10-skills-impact/) ran 6 repeats of each of 3 tasks. Its review ([REPORT.md](../2026-10-skills-impact/REPORT.md)) found that repeats of one task tell you how variable the agent is on that task, not whether a pack helps on tasks in general. Its pass-rate result rested on a single task (Codex on CROSS), and two of its three tasks were at the ceiling for the control.

This experiment keeps the question and the arms, drops Cursor (no credits), and spends the runs on many different tasks instead of repeats.

## Question

On a varied set of real change tasks, do Superpowers or Matt Pocock's skills raise the share of changes that pass independent acceptance tests, and at what cost in tokens?

## Agent and repository

- Codex `gpt-5.6-luna`, reasoning effort high, with the same clean home, isolation and rig version as skills-impact.
- shopizer at `6a4a0a6`. The verifier, isolation and hardened `summarize.py` are reused from skills-impact.

## Arms

`none`, `placebo`, `superpowers` and `pocock`, built exactly as in skills-impact (same pinned commits, same `AGENTS.md` bootstrap for Superpowers). pstack is left out because it ships only for Cursor and Claude Code.

## Tasks

17 candidate tasks, none reused from skills-impact. Most are **real defects found in shopizer** by probing its REST API (marked *real*): the bug is in upstream code at `6a4a0a6`, so no plant is needed. One is a planted two-cause bug, and the rest are small features. Each task has a prompt written the way a merchant, developer or support team would put it, an API-level hidden test, and a reference patch.

| ID | Kind | What is wrong or wanted | Causes the reference touches |
| --- | --- | --- | --- |
| `PAGE` | Bug (*real*) | `GET /api/v2/products?page=N` ignores the page | API binds no `page` parameter |
| `CONTENT` | Bug (*real*) | Listing content pages or boxes without paging parameters answers 500 | Two endpoints declare `int page, int count` with no defaults |
| `AMBIG` | Bug (*real*) | `GET /api/v1/category/{id}` and `/{friendlyUrl}` both answer 500 | Two handler mappings are ambiguous |
| `AVAIL` | Bug (*real*) | A product created with `available: false` comes back available | Mapper copies `visible` into `available` |
| `ADDR` | Bug (*real*, several causes) | PATCHed delivery address loses its street, and the state lands in the postal code | Three copy-paste slips in the facade's fallback code, plus the populator in two places |
| `CUSTDUP` | Bug (*real*) | Registering or admin-creating a customer with an email in use answers 500 | Exception with no handler; admin path throws the wrong exception |
| `CUSTPAGE` | Bug (*real*, several causes) | Admin customer list repeats customers across pages; totals wrong | API treats page as an offset; repository over-fetches; facade sets no totals |
| `NOTFOUND` | Bug (*real*) | Missing manufacturer answers 503, missing product 400 | API catch-all; service throws instead of returning nothing |
| `MANINUSE` | Bug (*real*) | Deleting a manufacturer still used by products answers 503 | No usage check before delete |
| `CATDUP` | Bug (*real*) | A duplicate category code (create or rename) answers 500 with a raw SQL error | No uniqueness check; no 409 mapping |
| `CARTCALC` | Bug (planted, two causes) | Line subtotals and cart totals ignore quantities | Two independent slips: cart mapper (line subtotal) and core order service (cart subtotal) |
| `TAXRATE` | Validation feature | Tax rates must be 0 to 100 on create and update (400, nothing stored) | The error handler crashes on a `ServiceRuntimeException` with no cause, so the obvious exception gives 500 |
| `REVIEW` | Validation feature | Review rating 1 to 5 (400), one review per customer (409) | Wrong status codes and a missing lower bound |
| `CATCOUNT` | Feature | Category `productCount` counts products in the category and its subcategories, each once | New repository query, service, facade |
| `MANORDER` | Feature | Store and return manufacturer `order`; list sorted by order, then code, across pages | Populator drops the field; paged query unsorted |
| `CUSTSEARCH` | Feature | Admin customer list filters: email, name and country, case-insensitive, combinable | API parameters; the repository's name clause lacks parentheses, so its `or` breaks combined filters |
| `TAXPAGE` | Feature | Tax rate list honours page and count, sorted by code, with correct totals | Facade overload and API wiring |

How each task is checked (`scripts/validate.py`, results in `tasks/<ID>/validation.json`):

- The hidden test fails on the starting code and passes with the reference.
- With the reference applied, the full reactor suite passes, including the hidden test.
- For the planted task, the existing suite still passes with the plant, so the plant gives no visible hint.

Three tests were strengthened after a deliberately wrong fix passed them; this is recorded in the amendment log.

**Selection (fixed before calibration):** `none` runs each candidate twice in calibration, and those runs are discarded. The 16 candidates with the lowest calibration pass rate are kept, with ties broken by alphabetical task id.

## Size and cost

16 tasks × 4 arms × 2 runs = **128 runs**, plus 34 calibration runs. At skills-impact's measured Codex cost ($0.08 a run without skills, $0.18 with Superpowers), that is about **$15 to $20**.

Two runs per task, not one, so that within-task noise can be estimated. The unit of analysis is the task.

## Measures

- **Primary:** verified pass (the hardened `summarize.py`: the build ran, every hidden test ran and passed, nothing skipped, no other test failed).
- **Secondary:**
  - tokens (fresh input, cached input and output reported separately);
  - wall time;
  - Maven test runs;
  - production lines and test lines changed;
  - skill uptake;
  - test-file-first and confirmed TDD (`process.py` from skills-impact);
  - overclaims.

## Hypotheses and analysis (fixed now)

| # | Hypothesis | Test |
| --- | --- | --- |
| T1 | Superpowers raises the pass rate | Per task, the difference in passes between `superpowers` and `none` (each 0 to 2). A one-sided exact sign-flip permutation test over tasks, with α = 0.05. The effect is reported as the mean per-task difference with a bootstrap interval over tasks |
| T2 | Pocock raises the pass rate | As T1 |
| T3 | Placebo has no effect (a check on T1 and T2) | As T1, two-sided, reported only |

- T1 and T2 are Holm-adjusted together.
- A pack's gain counts as a pack effect only if it is larger than the placebo's.
- Tokens are reported as the mean per-task ratio to `none`.
- Exploratory, labelled as such: results by task type, and Pocock conditional on a skill being read.

## Known limits

- One repository and one agent. Claude writes the tasks, plants, reference patches and hidden tests, and they are committed for review.
- Planted bugs are not real bugs, and a model trained on shopizer may know the original code.

## Amendment log

- 2026-10-21: draft written at the user's request ("increase the number of different tests, not the number of runs"; Codex only).
- 2026-10-21 (before calibration), tasks built:
  - 17 candidates instead of the planned ~20. Probing turned up enough real upstream defects that planted bugs were needed for only one task.
  - Dropped during building:
    - `PROMO`: applying any promo code fails under JDK 21 because of a reflection error in the rules engine, so the task could not be graded;
    - `PRICEPATCH`: it depended on a second, unrelated defect;
    - `CATVIS` and `STOREPAGE`: not real defects, or not testable without heavy setup.
  - Tests changed while building:
    - `CATCOUNT` dropped its availability rule, because product creation ignores `available`, which is task `AVAIL`.
    - `CATCOUNT` reads counts through the category list, because `GET /category/{id}` is broken (task `AMBIG`).
    - `CUSTSEARCH` gained combined-filter cases after a version of the fix without the parentheses passed the first draft of the test.
    - `MANORDER`'s test had a prefix clash in its own data, which was fixed.
  - The arms are byte-identical to skills-impact's, rebuilt from the same pinned commits. `trial.toml` and `calibration.toml` are generated by `scripts/make_trial.py`.
  - `CARTCALC` was re-planted. Its first plant (a cart item count of lines instead of units) broke an existing cart test, so the agent would have seen it. The second slip is now in the line subtotal, which no existing test covers, and the full suite passes with the plant.

