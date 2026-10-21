## 1. Preregistered tests: effect sizes and multiple comparisons

The tests and their raw p-values are exactly those in `analysis.md`. Added here: the difference in rates with a Newcombe 95% interval, and Holm-adjusted p-values across the nine preregistered tests (H1, H2, H7, three H4, three H5). H6 was descriptive. Test-first is reported under its new name, test-file-first.

| # | comparison | pack | none | difference (95% CI) | p | Holm p |
| --- | --- | --- | --- | --- | --- | --- |
| H1 | superpowers pass, BUG+CROSS | 24/24 | 22/24 | +8 pts (-7 to +26) | 0.245 | 0.979 |
| H2 | pocock pass, BUG+CROSS | 19/24 | 22/24 | -12 pts (-33 to +9) | 0.951 | 1.000 |
| H7 | pstack pass, Cursor | 18/18 | 18/18 | +0 pts (-18 to +18) | 1.000 | 1.000 |
| H4 | superpowers: BUG test that bites (original) | 12/12 | 8/12 | +33 pts (+2 to +61) | 0.047 | 0.280 |
| H4 | pocock: BUG test that bites (original) | 12/12 | 8/12 | +33 pts (+2 to +61) | 0.047 | 0.280 |
| H4 | pstack: BUG test that bites (original) | 5/6 | 8/12 | +17 pts (-28 to +47) | 0.439 | 1.000 |
| H5 | superpowers: test-file-first | 31/36 | 0/36 | +86 pts (+68 to +94) | 0.000 | 0.000 |
| H5 | pocock: test-file-first | 10/36 | 0/36 | +28 pts (+12 to +44) | 0.000 | 0.004 |
| H5 | pstack: test-file-first | 6/18 | 0/18 | +33 pts (+9 to +56) | 0.010 | 0.067 |

Reading the intervals: a pass-rate interval that includes 0 means no improvement was demonstrated. It is not evidence of no effect: the H1 interval also includes gains of the size shown by its upper bound.

## 2. Where the pass-rate evidence comes from (task clustering and ceiling)

The 6 runs in a cell repeat one task. The independent units for generalising to other tasks are the 3 tasks (6 task-agent cells), not the runs. Pass rate per task-agent cell:

| task | agent | none | placebo | superpowers | pocock | pstack |
| --- | --- | --- | --- | --- | --- | --- |
| BUG | codex | 6/6 | 4/6 | 6/6 | 5/6 | - |
| BUG | cursor | 6/6 | 6/6 | 6/6 | 5/6 | 6/6 |
| CROSS | codex | 4/6 | 4/6 | 6/6 | 4/6 | - |
| CROSS | cursor | 6/6 | 6/6 | 6/6 | 5/6 | 6/6 |
| FEAT | codex | 6/6 | 6/6 | 6/6 | 6/6 | - |
| FEAT | cursor | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |

`none` passed every run in 5 of 6 task-agent cells. A pack can only show a gain where the control fails, which here is one cell: Codex on CROSS (4/6). Every pass-rate difference in favour of a pack comes from that cell.

- Codex CROSS, superpowers 6/6 vs none 4/6: difference +33 pts (-12 to +70), one-sided p 0.227.
- Codex CROSS, placebo 4/6 vs none 4/6: difference +0 pts (-44 to +44), one-sided p 0.727.
- Codex CROSS, pocock 4/6 vs none 4/6: difference +0 pts (-44 to +44), one-sided p 0.727.
- Exploratory, Codex only, BUG+CROSS: superpowers 12/12 vs none 10/12, difference +17 pts (-10 to +45), one-sided p 0.239.

## 3. Pocock: did the skills run?

| task | agent | runs that read a Pocock skill | passed when read | passed when not read |
| --- | --- | --- | --- | --- |
| BUG | codex | 6/6 | 5/6 | 0/0 |
| BUG | cursor | 6/6 | 5/6 | 0/0 |
| CROSS | codex | 0/6 | 0/0 | 4/6 |
| CROSS | cursor | 1/6 | 1/1 | 4/5 |
| FEAT | codex | 1/6 | 1/1 | 5/5 |
| FEAT | cursor | 4/6 | 4/4 | 2/2 |

Exploratory and confounded with task: reading a skill is almost entirely determined by which task it is. The H2 result is a test of the pack as installed. On CROSS and FEAT it says little about Pocock's instructions, which mostly were never read.

## 4. Tests that bite, per defect (retrospective)

Control: the hidden test, run through the same harness, is classified `both` (it detects each defect on its own and passes on the fixed code).

| agent | arm | both | price-only | mapper-only | combined-only | none | fails-on-fixed | not-executable | no-tests |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex | none | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| codex | placebo | 4 | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| codex | superpowers | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| codex | pocock | 5 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| cursor | none | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 4 |
| cursor | placebo | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 5 |
| cursor | superpowers | 5 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| cursor | pocock | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| cursor | pstack | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |

- Exploratory: superpowers runs whose tests catch both defects independently, 11/12 vs none 6/12: difference +42 pts (+5 to +67), one-sided p 0.034.
- Exploratory: pocock runs whose tests catch both defects independently, 8/12 vs none 6/12: difference +17 pts (-20 to +48), one-sided p 0.340.
- Exploratory: pstack runs whose tests catch both defects independently, 5/6 vs none 0/6: difference +83 pts (+28 to +97), one-sided p 0.008.
- codex none: 6/6 catch both defects.
- codex superpowers: 6/6 catch both defects.
- cursor none: 0/6 catch both defects.
- cursor superpowers: 5/6 catch both defects.
On Codex the control already caught both defects in every run, so the pooled gaps come from Cursor, where `none` rarely wrote a test at all.

The four failed BUG runs: `BUG/placebo/codex/1` price-only; `BUG/placebo/codex/6` mapper-only; `BUG/pocock/codex/2` price-only; `BUG/pocock/cursor/6` price-only.

## 5. Test-file-first and evidence of TDD (retrospective)

| agent | arm | test-file-first (H5) | tdd-confirmed | test-file-first | impl-first | no-test-edits | unknown |
| --- | --- | --- | --- | --- | --- | --- | --- |
| codex | none | 0/18 | 0 | 0 | 8 | 10 | 0 |
| codex | placebo | 0/18 | 0 | 0 | 9 | 9 | 0 |
| codex | superpowers | 17/18 | 13 | 4 | 0 | 0 | 1 |
| codex | pocock | 7/18 | 6 | 0 | 6 | 5 | 1 |
| cursor | none | 0/18 | 0 | 0 | 2 | 16 | 0 |
| cursor | placebo | 0/18 | 0 | 0 | 2 | 16 | 0 |
| cursor | superpowers | 14/18 | 6 | 6 | 4 | 0 | 2 |
| cursor | pocock | 3/18 | 1 | 2 | 6 | 9 | 0 |
| cursor | pstack | 6/18 | 4 | 0 | 3 | 4 | 7 |

Why runs were not confirmed: pocock test-file-first (no test run before the fix) ×2; pocock unknown (test run output does not name the failing class) ×1; pstack unknown (subagent) ×5; pstack unknown (test run output does not name the failing class) ×1; pstack unknown (unreadable shell edit) ×1; superpowers test-file-first (compile error only) ×9; superpowers test-file-first (no test run before the fix) ×1; superpowers unknown (test run output does not name the failing class) ×3.

- Exploratory: superpowers confirmed TDD in 19/36 runs (3 unknown) vs none 0/36: difference +53 pts (+34 to +68).
- Exploratory: pocock confirmed TDD in 7/36 runs (1 unknown) vs none 0/36: difference +19 pts (+6 to +35).
- Exploratory: pstack confirmed TDD in 4/18 runs (7 unknown) vs none 0/18: difference +22 pts (+0 to +45).

## 6. Cost and effort (reconciled)

Two relative-cost figures were published and they use different methods. `report.md` (the rig) divides each run's tokens by the `none` **mean** for the same task and agent, then averages. `analysis.md` takes the **median** of each run's tokens divided by the `none` median. Both are shown. Token totals include cached input; Codex counts cached input inside input, Cursor separately.

| agent | arm | runs | mean total tokens | mean fresh input | mean cached input | mean output | relative (mean method) | relative (median method) | est. $ total | passes | est. $ per verified pass | median s | median Maven test runs | median production lines | median test lines |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex | none | 18 | 2.17M | 0.10M | 2.06M | 12k | 1.00 | 1.00 | 1.37 | 16 | 0.086 | 134 | 2 | 50 | 0 |
| codex | placebo | 18 | 2.56M | 0.11M | 2.44M | 13k | 1.16 | 1.25 | 1.57 | 14 | 0.112 | 161 | 1 | 46 | 25 |
| codex | superpowers | 18 | 5.86M | 0.20M | 5.65M | 19k | 2.62 | 2.77 | 3.15 | 18 | 0.175 | 307 | 7 | 44 | 128 |
| codex | pocock | 18 | 2.97M | 0.12M | 2.84M | 14k | 1.41 | 1.74 | 1.76 | 15 | 0.117 | 192 | 4 | 42 | 74 |
| cursor | none | 18 | 0.52M | 0.06M | 0.45M | 9k | 1.00 | 1.00 | 19.29 | 18 | 1.072 | 118 | 0 | 50 | 0 |
| cursor | placebo | 18 | 0.49M | 0.07M | 0.41M | 8k | 0.96 | 1.05 | 18.18 | 18 | 1.010 | 116 | 0 | 41 | 0 |
| cursor | superpowers | 18 | 0.98M | 0.09M | 0.88M | 11k | 1.93 | 2.33 | 35.87 | 18 | 1.993 | 170 | 2 | 51 | 74 |
| cursor | pocock | 18 | 0.66M | 0.08M | 0.57M | 9k | 1.33 | 1.49 | 24.53 | 16 | 1.533 | 149 | 0 | 38 | 20 |
| cursor | pstack | 18 | 1.18M | 0.12M | 1.05M | 14k | 2.38 | 2.75 | 43.56 | 18 | 2.420 | 206 | 2 | 44 | 38 |

Dollar figures are estimates at list prices: Codex $0.20, $0.02 and $1.20 per million fresh-input, cached-input and output tokens; Cursor $2 per million for all input including cache reads (the design's rule, an upper bound) and $6 per million output. Nothing here is a billed amount. Cost per verified pass is total estimated spend divided by passing runs. With most cells at the ceiling it mostly restates relative cost, and it is not a measure of value.

Attribution: the logs show that pack runs make more turns and more Maven test runs and add test code, while the production change stays the same size. They do not show what share of the extra tokens each of those causes, because most tokens are context re-sent on every turn.

## 7. Grading and isolation audits

- Independent regrade from the Maven logs: agrees with the recorded grade on 162/162 runs.
- Hidden suites ran their full count with nothing skipped in 162/162 runs.
- `none` and `placebo` runs with any trace of a pack skill in their event logs: 0/72.
