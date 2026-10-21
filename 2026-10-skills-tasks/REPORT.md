# Skill packs across 16 different tasks (Codex, low effort): report

Run on 2026-10-21. The design, hypotheses and selection rule are in [README.md](README.md), written before the measured runs. The raw runs are in [results/stage1](results/stage1/), the analysis is in [results/analysis.md](results/analysis.md) (produced by `scripts/analyse.py`), and the rig's own summary is in [results/report.md](results/report.md).

## Summary

- **No pack measurably raised the pass rate.**
  - Superpowers passed 24 of 32 runs, the same as the control.
  - Pocock passed 27 of 32 runs: 4 tasks better, 1 worse, +9.4 points. That is inconclusive (Holm p = 0.38): the interval runs from −3 to +22 points, and every gain was a single run on a task.
  - The placebo passed 23 of 32.
  - This is no *measured* improvement, not evidence that the packs have no benefit.
- **Superpowers changed how the agent worked and cost about three times as much.**
  - It wrote tests in 23 of 32 runs (the control wrote none) and ran Maven in 28 of 32 runs (the control ran Maven once).
  - It used 3.07 times the control's tokens per task (2.50 to 3.68). Pocock used 1.57 times (1.10 to 2.24).
- **More process did not mean more correct changes.** Superpowers ran the test suite in 28 of 32 runs against 1 of 32 for the control, and passed the same number.
- **On one task, the arm that tested against the running API got it right.** This is a plausible mechanism, not proof that testing caused it: the pack changed other behaviour too, and only one run is confirmed test-first.
  - On `TAXRATE`, the control and the placebo added validation annotations that nothing enforces and failed all four runs. Superpowers passed both of its runs. Both wrote an integration test that calls the endpoint and added a range check in the API; one run is confirmed to have seen its test fail before the fix (the other is unknown).
  - On `ADDR`, `CARTCALC` and `PAGE`, Superpowers did worse than the control.
- **Nearly every failure came with a claim of success.** In 28 of the 30 failed runs, the agent said its change worked. This held in every arm, so no pack fixed it.
- **One task beat every arm.** All 8 runs on `HREVIEW` failed, and 7 of them broke creating a review, which had worked before the change.

These results are at **low** reasoning effort and are not directly comparable with [skills-impact](../2026-10-skills-impact/), which used high effort (see "What changed from the design").

## Setup

| | |
| --- | --- |
| Agent | Codex `gpt-5.6-luna`, reasoning effort low, clean home, the same isolation as skills-impact |
| Repository | shopizer at `6a4a0a6` (Java, Maven, JDK 21) |
| Arms | `none`, `placebo` (a generic "careful engineering" skill), `superpowers`, `pocock`, byte-identical to skills-impact's. The placebo is not inert: it holds real general guidance (understand the call path, consider edge cases, keep changes small), so it is better read as a *generic-guidance* arm. The packs are adapted to Codex's skill layout, and Superpowers gets its bootstrap through `AGENTS.md` |
| Tasks | 16, chosen from a pool of 18 by a rule fixed before calibration: 10 real upstream bugs, 1 planted bug, 5 features |
| Runs | 16 tasks × 4 arms × 2 = 128, all completed (status `ok`, no timeouts) |
| Grading | Hidden API-level JUnit tests the agent never saw, plus the full existing suite. A run passes only if every hidden test ran and passed and no other test failed |
| Spend | $2.95 at list prices for the 128 runs (the design estimated $15 to $20, based on high-effort runs) |

## Results by task

Passes out of 2:

| task | kind | none | placebo | superpowers | pocock |
| --- | --- | --- | --- | --- | --- |
| ADDR | real bug | 1 | 1 | 0 | 1 |
| AMBIG | real bug | 2 | 2 | 2 | 2 |
| AVAIL | real bug | 2 | 2 | 2 | 2 |
| CARTCALC | planted bug | 2 | 2 | 1 | 2 |
| CATCOUNT | feature | 2 | 0 | 2 | 1 |
| CATDUP | real bug | 2 | 2 | 2 | 2 |
| CONTENT | real bug | 1 | 2 | 2 | 2 |
| CUSTDUP | real bug | 2 | 1 | 2 | 2 |
| HCUST | feature | 1 | 2 | 1 | 2 |
| HREVIEW | real bug | 0 | 0 | 0 | 0 |
| MANCODE | feature | 2 | 2 | 2 | 2 |
| MANINUSE | real bug | 2 | 2 | 2 | 2 |
| MANORDER | feature | 2 | 2 | 2 | 2 |
| NOTFOUND | real bug | 1 | 1 | 1 | 2 |
| PAGE | real bug | 2 | 2 | 1 | 2 |
| TAXRATE | feature | 0 | 0 | 2 | 1 |
| **total** | | **24/32** | **23/32** | **24/32** | **27/32** |

Six tasks were passed by every run, and one (`HREVIEW`) by none. The arms differ only on the other nine, and most of those differences are a single run.

No run in any arm broke an existing test. Every failure is a hidden-test failure.

## Preregistered tests

Each task contributes one number: a pack's passes minus the control's passes, from −2 to +2. The test is an exact sign-flip permutation over the 16 tasks. T1 and T2 are one-sided and Holm-adjusted together; T3 is two-sided.

| # | pack vs none | tasks better / same / worse | mean difference in pass rate (95% CI over tasks) | p | Holm p |
| --- | --- | --- | --- | --- | --- |
| T1 | superpowers | 2 / 11 / 3 | +0.0 pts (−15.6 to +18.8) | 0.625 | 0.625 |
| T2 | pocock | 4 / 11 / 1 | +9.4 pts (−3.1 to +21.9) | 0.188 | 0.375 |
| T3 | placebo | 2 / 12 / 2 | −3.1 pts (−21.9 to +12.5) | 1.000 | - |

Neither T1 nor T2 is supported. The placebo moved results on 4 of 16 tasks, about as often as the packs did. So a one-run swing on a task is within the noise of two runs at low effort.

Only 9 of the 16 tasks separate the arms at all. Six were passed by every run and `HREVIEW` was failed by every run, so the effective sample is smaller than it looks.

For Pocock, the pre-planned exploratory check does not point to the skills:

- 23 of the 27 runs that read a Pocock skill passed;
- 4 of the 5 runs that read none passed.

## Cost and process

| arm | mean tokens | token ratio vs none per task (95% CI) | mean $ per run | median seconds | runs that ran Maven tests | runs that wrote tests | test-file-first | confirmed TDD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| none | 0.37M | 1.00 | 0.016 | 43 | 1/32 | 0/32 | 0/32 | 0/32 |
| placebo | 0.40M | 1.09 (0.96 to 1.22) | 0.017 | 47 | 2/32 | 0/32 | 0/32 | 0/32 |
| superpowers | 1.09M | 3.07 (2.50 to 3.68) | 0.038 | 105 | 28/32 | 23/32 | 21/32 | 9/32 |
| pocock | 0.54M | 1.57 (1.10 to 2.24) | 0.021 | 54 | 8/32 | 2/32 | 1/32 | 0/32 |

- Test-file-first means the first file edited was a test. Confirmed TDD also requires that the test was run and seen to fail before the production change. The definitions are in skills-impact's `process.py`.
- Superpowers' cost ratio (3.1x) matches skills-impact at high effort (2–3x). In both experiments, Superpowers mostly changed the process and the cost, not the outcome.
- At low effort, the control almost never tests its own change: it ran Maven tests in 1 of 32 runs.
- Pocock read a skill in 27 of 32 runs and the placebo in all 32. The placebo reads cost little (1.09x).

## Exploratory analysis, added after the results

Added on 2026-10-21 after an external review, so it is not part of the preregistered analysis. The contrasts were chosen after seeing the data, so the p values are descriptive only. The numbers are in [results/analysis.md](results/analysis.md).

**Packs against the generic-guidance arm.** The design said a pack counts only if it beats the placebo, but tested each pack only against `none`.

| pack vs placebo | tasks better / same / worse | mean per-task difference in pass rate | p (two-sided) |
| --- | --- | --- | --- |
| superpowers | 3 / 9 / 4 | +3.1 pts | 1.000 |
| pocock | 4 / 12 / 0 | +12.5 pts | 0.125 |

- Pocock never did worse than the generic-guidance arm. But only 4 tasks differ, so the exact test cannot go below p = 0.125. A bootstrap interval over so few differing tasks is not reliable, so I don't give one.
- This is a lead for the next experiment, not a result.

**Cost per verified success.** This is a better decision measure than the token ratio alone, because it charges failed runs to the arm that produced them.

| arm | verified passes | total $ | $ per verified pass | tokens per verified pass | minutes per verified pass |
| --- | --- | --- | --- | --- | --- |
| none | 24/32 | 0.50 | 0.021 | 0.50M | 1.0 |
| placebo | 23/32 | 0.55 | 0.024 | 0.56M | 1.1 |
| superpowers | 24/32 | 1.22 | 0.051 | 1.46M | 2.3 |
| pocock | 27/32 | 0.68 | 0.025 | 0.64M | 1.2 |

Superpowers costs about 2.4 times as much as the control per verified change and takes about 2.3 times as long. Pocock's extra passes bring its cost per success close to the control's.

**Effort may matter more than skills.** `HREVIEW` passed 2 of 2 at high effort in calibration (`results/calibration-high.md`) and 0 of 8 at low effort here, across all four arms. That is a clue, not a controlled comparison: the runs were different, and there are 2 against 8.

## What went wrong, by task

The failing hidden assertions are tallied from each run's `verify-mvn.log.gz`.

### TAXRATE: annotations that nothing enforces

The task: tax rates outside 0 to 100, or missing, must answer 400.

The obvious fix is `@DecimalMin`, `@DecimalMax` and `@NotNull` on `PersistableTaxRate`. The API never validates that object, so those annotations do nothing. Five failing runs left the out-of-range creates and updates answering **200**. A missing rate answered **500**.

Every passing run threw `RestApiException` or `ResponseStatusException` from code:

- **Superpowers, 2 of 2.** Both runs wrote a test (26 and 46 lines) and ran it.
- **Pocock, 1 of 2.** The passing run wrote no test.

Of all the tasks, this is the one where checking at runtime separates the arms. It is also the only task where any arm went from 0/2 to 2/2.

### HREVIEW: the fix broke creating a review

The task has six causes: a path-variable mismatch, an edit that never sets the id, duplicate description rows, a rating adjusted only on create, a delete that never recomputes, and a lazy proxy that gives 503 instead of 404.

All eight runs failed. In seven of them, the hidden test could no longer **create** a review, which worked on the starting code (201 before the change, 503 after).

I reproduced one run (`none`, run 1) in a scratch checkout, and the cause is the shared review populator:

- To support edits, the agents made it load the existing review by id.
- On create, the id is 0, so the lookup throws `EntityNotFoundException: Unable to find ProductReview with id 0`.
- The API's catch-all turns that exception into 503.

No existing test covers review creation, so the run's own checks stayed green. I hit the same trap while writing the reference patch, which guards the lookup with `id > 0`.

The eighth run (Pocock, run 2) kept create working but did not touch the API, so edit and delete still answered 500.

### The other failures

| Task | What the failing runs got wrong |
| --- | --- |
| `ADDR` (5 of 8 runs failed, 2 of them Superpowers) | Fixed only part of the copy-paste chain: the delivery street stayed "1 Main Street", and in two runs the state stayed empty |
| `NOTFOUND` (3 failed) | A missing product still answered 400, because the service throws instead of returning nothing |
| `CATCOUNT` (3 failed: placebo 2, Pocock 1) | A product in several subcategories was counted once per subcategory |
| `HCUST` (2 failed) | Every search request answered 500, so the change broke the list endpoint itself |

### Saying it worked when it had not

- The rig asks each agent to state whether its change works. In 28 of the 30 failed runs, the agent said it did:
  - `none`: 7 of 8;
  - `placebo`: 9 of 9;
  - `superpowers`: 7 of 8;
  - `pocock`: 5 of 5.
- The agent could not see the hidden tests.
- These claims rested on compiling, on the existing suite, or (for Superpowers) on tests the agent wrote itself that passed. None of those caught the failures.

## How far the result goes

- **Sixteen tasks are too few for effects of this size.** The per-task differences for Pocock have a standard deviation of about 0.27 (in pass-rate units). A real +9-point effect would need roughly 65 tasks to reach 80% power at this α. The interval cannot rule out effects of that size, but it does rule out a gain of more than about 22 points from either pack on tasks like these.
- **Two runs per task is coarse.** The placebo, which has no specialist content, changed 4 tasks by one run each.
- **Few tasks separate the arms.** Picking the 16 hardest of only 18 candidates did little to avoid ceiling and floor effects: 7 tasks scored the same in every arm.
- **Codex only.** The packs were adapted to Codex's skill layout. This says nothing about how they perform in their original Claude Code setting.
- **One repository and one agent at one effort level.** I wrote the tasks, reference patches and hidden tests, and they are committed so others can check them. Ten of the bugs are real upstream defects, and one is planted.
- **Not comparable with skills-impact on pass rate.** That experiment ran at high effort, where the control passed 32 of 34 calibration runs on this pool. The cost and process findings do line up.

## What changed from the design

The design changes are all logged in the README, with dates, and were made before any measured run:

- the switch to low effort;
- the three hard tasks;
- `CUSTPAGE` and `CUSTSEARCH` folded into `HCUST`.

Calibration kept the 16 tasks below. It dropped `REVIEW` and `TAXPAGE`, both 2/2, by the alphabetical tie-break.

The selection rule was applied as written ([results/calibration.md](results/calibration.md)):

| Calibration result (control, 2 runs) | Tasks |
| --- | --- |
| 0/2 | `HREVIEW`, `TAXRATE` |
| 1/2 | `ADDR`, `CONTENT`, `CUSTDUP`, `HCUST`, `NOTFOUND` |
| 2/2, kept | the other 9 |

After the runs, an exploratory section was added following an external review: packs against the placebo, cost per verified success, and the effort clue. It is labelled as such, and the preregistered tests are unchanged. Wording was also tightened: the placebo is now described as an active generic-guidance arm, Pocock as inconclusive, and the TAXRATE testing evidence as a plausible mechanism, not a cause.

One other change after the runs, to presentation only: `analyse.py` printed the T3 row without its first columns, because of a misplaced conditional expression. I fixed that line and reran the script. The statistics were not changed.

## Suggested next step

A 60-task repeat would size the Pocock signal more precisely, but it would leave the more useful causal question open. A smaller, targeted design would separate the effect of verification, of a full pack and of reasoning effort:

| arm | configuration | what it isolates |
| --- | --- | --- |
| A | no skills, low effort | baseline |
| B | a short instruction to verify against the running API, low effort | value of explicit verification |
| C | Superpowers, low effort | what the full pack adds |
| D | no skills, high effort | value of more reasoning |

- **Tasks.** Use runtime-trap tasks such as `TAXRATE`, `HREVIEW`, `ADDR` and `HCUST`, plus new tasks where the fix must keep neighbouring behaviour working.
- **Difficulty.** Some tasks must still be hard at high effort, or arm D will sit at the ceiling: high effort passed 32 of 34 in calibration.
- **Runs.** Use more runs per task, randomise run order, and keep the hidden verifier.
- **Measures.** Report cost and time per verified success.
- **Hypothesis.** Explicit verification against executable behaviour gives more correctness per unit of cost than a broad skill pack.

## Reproducing

```
scripts/build_arms.sh                     # rebuild the arms from pinned commits
scripts/localize.sh                       # write trial.local.toml for your home folder
trialrig run trial.local.toml --out <dir> --agent codex
scripts/export.sh <dir> stage1
python3 -I scripts/analyse.py results/stage1/runs > results/analysis.md
```

`scripts/validate.py <ID> --full` re-checks each task:

- the hidden test fails on the start;
- it passes with the reference;
- the full suite passes;
- for `CARTCALC`, the plant leaves the existing suite green.
