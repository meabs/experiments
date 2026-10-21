# Results: do popular skill packs make agents better at changing code?

Stage 1, run on 2026-10-21: 162 runs, each of which finished with status `ok` (none crashed and none timed out). The full tables are in [analysis.md](analysis.md), the per-run data in [runs.csv](runs.csv), the rig's own report in [report.md](report.md), and the raw runs in [stage1/](stage1/).

## Answer

**No pack measurably raised the pass rate.** The packs did change how the agents worked: Superpowers made agents write tests first, and its runs never claimed a pass they had not earned. Those changes cost 2 to 3 times the tokens, and on these tasks they did not produce a statistically detectable gain in correct changes.

## Pre-registered hypotheses

| # | Hypothesis | Treatment | `none` | One-sided Fisher p | Result |
| --- | --- | --- | --- | --- | --- |
| H1 | Superpowers raises the pass rate (BUG + CROSS, both agents) | 24/24 | 22/24 | 0.245 | Not supported |
| H2 | Pocock raises the pass rate (BUG + CROSS, both agents) | 19/24 | 22/24 | 0.951 | Not supported (it was lower) |
| H7 | pstack raises the pass rate (Cursor, all tasks) | 18/18 | 18/18 | 1.000 | Not testable: Cursor was at the ceiling |
| H4 | Superpowers produces tests that bite (BUG) | 12/12 | 8/12 | 0.047 | Supported, narrowly* |
| H4 | Pocock produces tests that bite (BUG) | 12/12 | 8/12 | 0.047 | Supported, narrowly* |
| H4 | pstack produces tests that bite (BUG) | 5/6 | 8/12 (Cursor alone: 2/6) | 0.439 | Not supported |
| H5 | Superpowers works test-first (all change runs) | 31/36 | 0/36 | < 0.001 | Supported |
| H5 | Pocock works test-first | 10/36 | 0/36 | < 0.001 | Supported |
| H5 | pstack works test-first (Cursor) | 6/18 | 0/18 | 0.010 | Supported |
| H6 | The packs reduce overclaiming (descriptive) | Superpowers 0, pstack 0, Pocock 4 | 2 (placebo: 3) | - | Superpowers and pstack: no overclaims |

The placebo arm (generic advice with nothing about testing) passed 20/24 and was never test-first (0/36). The process effects therefore come from the packs' content, not from "more instructions in context".

\* H4: every test any agent wrote failed on the unfixed code (44 of 44 runs that wrote tests). The difference between arms is therefore entirely whether a test was written at all, not how good it was. Three H4 comparisons were made, and p = 0.047 would not survive a correction for that. pstack runs only on Cursor, where `none` wrote a test in just 2 of 6 BUG runs.

## Per agent

| Agent | Arm | Pass | Tokens vs `none` (median) | Mean $ per run | Skill read | Added tests | Test-first | Overclaims |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Codex (Luna) | none | 16/18 | 1.00x | 0.08 | - | 7/18 | 0 | 2 |
| | placebo | 14/18 | 1.25x | 0.09 | 18/18 | 9/18 | 0 | 3 |
| | superpowers | **18/18** | 2.77x | 0.18 | 18/18 | 17/18 | 17 | 0 |
| | pocock | 15/18 | 1.74x | 0.10 | 7/18 | 13/18 | 7 | 3 |
| Cursor (Grok 4.7 low) | none | 18/18 | 1.00x | 1.07 | - | 2/18 | 0 | 0 |
| | placebo | 18/18 | 1.05x | 1.01 | 18/18 | 2/18 | 0 | 0 |
| | superpowers | 18/18 | 2.33x | 1.99 | 18/18 | 18/18 | 14 | 0 |
| | pocock | 16/18 | 1.49x | 1.36 | 11/18 | 9/18 | 3 | 1 |
| | pstack | 18/18 | 2.75x | 2.42 | 18/18 | 12/18 | 6 | 0 |

Cursor dollar figures charge cached input at the full $2 per million, as the design said. That is an upper bound; see "Cost" below. Token counts are not comparable between agents.

## What the failures were

There were 11 failures, all on Codex except 2 Cursor Pocock runs. Each was checked by hand, and none was an infrastructure fault:

- **BUG, 4 runs** (placebo ×2, Pocock ×2): the agent fixed only one of the two planted slips. Each wrote a unit test that proved its half-fix and claimed a pass. The merchant's symptom was still there.
- **CROSS, 5 runs** (`none` ×2, placebo, Pocock ×2): the invalid website was still accepted. The usual cause was an `@Pattern` annotation, which never runs because shopizer has no bean-validation provider.
- **CROSS, 2 runs** (placebo, Pocock): the agent added `spring-boot-starter-validation` so that `@Pattern` would run. That switched on validation across the whole API and broke two existing tests for creating categories and products, so the change was a regression.

Superpowers was the only arm with no failures on Codex, including CROSS (6/6 against 4/6 for `none`). At 6 runs a cell, that difference is not significant.

## Did the skills get used?

- **Superpowers, placebo and pstack** were read in every run (Superpowers' bootstrap is in `AGENTS.md`, and pstack is invoked by the prompt prefix).
- **Pocock** was read in 18 of 36 runs: in every BUG run, but in only 1 of 12 CROSS runs and 5 of 12 FEAT runs. Under the design's rule, the null result for Pocock on CROSS and FEAT means the skills were rarely triggered, not that they do not work.

## Cost

- Codex: **$7.85** for 72 runs.
- Cursor: 7.7M fresh input tokens, 60.4M cache reads and 0.9M output tokens over 90 runs. That is **$141** if cached input pays the full $2 per million (the design's assumption) and **$33 to $51** at typical cached-input rates ($0.20 to $0.50 per million). The real charge is on Cursor's usage dashboard.
- **The estimate was wrong.** The design expected 30k to 80k tokens per Cursor run; the median was 0.41M (`none`) to 1.20M (`pstack`), mostly cache reads. The total exceeded the $10 to $50 estimate if Cursor bills cache reads at full price.

## Stage 2

Not run. `trialrig plan` ([plan.md](plan.md)) marks every cell as futile: telling apart token differences under 20% would need 59 to 113 runs per arm, far over the cap of 12. The large differences are already clear. On pass rate, separating 24/24 from 22/24 would take hundreds of runs, and the Cursor ceiling would make extra runs uninformative.

## Limits

- Cursor (Grok 4.7 low) solved every task with no skills, so it cannot show a pass-rate gain. Only Codex had room to improve, giving 12 runs per arm on the hard tasks.
- FEAT was at the ceiling for both agents (kept for cost and process only, as decided before the run).
- Test-first is measured from edit order. Codex edits made through shell commands rather than `apply_patch`, and edits by pstack's subagents, are not seen. This can only undercount.
- Tests that bite was checked against the full plant. It does not show whether a test covered both slips; the 4 BUG failures show that some did not.
- One repository, Claude-written tasks and hidden tests, and cheap models. See the design's known limits.
