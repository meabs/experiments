# Does a skill add anything to an instruction to test? (Codex): report

Run on 2026-10-22 and 23. The design and hypotheses are in [README.md](README.md), committed before any measured run. The raw runs are in [results/stage1](results/stage1/) (arms A to D), [results/stage1-medium](results/stage1-medium/) (E) and [results/stage1-gate](results/stage1-gate/) (F). The analysis is in [results/analysis.md](results/analysis.md), from `scripts/analyse.py`. The rig's summaries are in [results/report-main.md](results/report-main.md), [results/report-medium.md](results/report-medium.md) and [results/report-gate.md](results/report-gate.md).

## Summary

- **A one-paragraph instruction was enough to get a real test.**
  - Told to add a focused API test that fails without the change and passes with it, the agent wrote one in 56 of 60 runs. With the task alone, it wrote one in none.
  - "Real" is checked by running the agent's own tests with its change and on the original code. Every relevant test passes with the change and at least one fails on the original. None counted only because it did not compile on the original.
- **The skill added nothing to the instruction. H1 and H2 are not supported.**

  | arm | relevant test |
  | --- | --- |
  | B instruction | 56/60 |
  | C instruction + original skill | 52/60 |
  | D instruction + revised skill | 54/60 |

  - The original skill did slightly worse than the instruction alone (H1, Holm p 1.0). The revised skill did slightly better than the original (H2, Holm p 1.0). Neither difference is measurable.
  - **The smoke-test shortcut did not come back.** In explicit-skills, told only to follow the skill, most runs ran `ActuatorTest` and stopped. Here, with a direct instruction alongside the same skill, no run in any arm ran only `ActuatorTest`. The shortcut came from the missing instruction, not from the skill's order.
- **A gate that sends the agent back worked as well as the instruction. H3 is not supported.**
  - Arm F got the task alone. When it tried to finish, a hook checked for a relevant test and, if there was none, sent it back once. The first check blocked all 60 runs: without being asked, the agent never wrote a test. After one block, 58 of 60 had a relevant test.
  - That is 2 more than the instruction (Holm p 1.0). The gate is at least as effective, and needs no change to the prompt.
- **Real tests did not measurably raise the pass rate.**

  | arm | passed |
  | --- | --- |
  | A none | 40/60 |
  | B instruction | 41/60 |
  | C skill | 41/60 |
  | D revised skill | 43/60 |
  | E medium effort | **49/60** |
  | F gate | 47/60 |

  - B, C and D wrote real tests in 52 to 56 runs, but passed 41 to 43, about the same as no test at all.
  - Medium effort, with no test, again gained most: 15 points over none (p 0.03, unadjusted, secondary).
  - The gate gained 12 points over none (p 0.15) and 10 over the instruction (p 0.22). Not significant, but the largest gain of any guided arm. In 20 gated runs, the agent changed the code itself after being sent back, not only tests (see "Exploratory").
- **Tests cost two to three times as much per correct change.** Cost per verified pass, against none: instruction 2.4 times, skill 3.0, revised skill 2.9, gate 2.5, medium effort 1.5.
- **Failed runs still mostly said they had worked:** 85 of 99 failed runs, across all arms. Writing a real test cut this only a little: 55 of 68 in the arms that wrote tests (B, C, D, F), against 30 of 31 in A and E.

## Setup

| | |
| --- | --- |
| Agent | Codex `gpt-5.6-luna` (CLI 0.157), reasoning effort low (E: medium), clean home, the same isolation as before |
| Repository | shopizer at `6a4a0a6` (Java, Maven, JDK 21), offline |
| Tasks | The 20 tasks of verify-vs-skills, repo-skills and explicit-skills, unchanged: 18 runtime traps and 2 neighbour breaks |
| Runs | 20 tasks × 6 arms × 3 = 360, all completed (status `ok`, no timeouts). A to D in one trial file, E and F each in their own, run side by side |
| Grading | Hidden API-level JUnit tests the agent never saw, plus the full existing suite. A run passes only if every hidden test passes and no other test fails. Before the hidden tests are added, the relevance check runs the agent's own tests with its change and on the original code |
| Spend | $15.12 at list prices |

The arms, the instruction, the revised skill and the gate are described in the [README](README.md#arms).

## Results

### Relevant tests (primary)

| # | comparison | tasks better / same / worse | mean per-task difference (95% CI) | Holm p |
| --- | --- | --- | --- | --- |
| H1 | skill vs instruction | 1 / 15 / 4 | −6.7 pts (−16.7 to +1.7) | 1.000 |
| H2 | revised skill vs skill | 3 / 15 / 2 | +3.3 pts (−5.0 to +13.3) | 1.000 |
| H3 | gate vs instruction | 4 / 14 / 2 | +3.3 pts (−5.0 to +11.7) | 1.000 |

Instruction against none (secondary): +93.3 points (+86.7 to +98.3), better on all 20 tasks.

Why the remaining runs had no relevant test:

| arm | no test of its own | its tests fail with the change | its tests also pass without the change |
| --- | --- | --- | --- |
| A none | 60 | 0 | 0 |
| B instruction | 0 | 4 | 0 |
| C skill | 0 | 7 | 1 |
| D revised skill | 0 | 4 | 2 |
| E medium effort | 60 | 0 | 0 |
| F gate | 0 | 1 | 1 |

Every run in B, C, D and F wrote a test and ran tests. The misses were tests left failing, or tests that did not check the change.

### Pass rate (secondary, two-sided, unadjusted)

| comparison | tasks better / same / worse | difference (95% CI) | p |
| --- | --- | --- | --- |
| instruction vs none | 3 / 13 / 4 | +1.7 pts (−10.0 to +15.0) | 1.000 |
| skill vs none | 3 / 12 / 5 | +1.7 pts (−11.7 to +16.7) | 1.000 |
| revised skill vs none | 6 / 9 / 5 | +5.0 pts (−11.7 to +23.3) | 0.717 |
| medium vs none | 6 / 14 / 0 | +15.0 pts (+5.0 to +26.7) | 0.031 |
| gate vs none | 6 / 12 / 2 | +11.7 pts (0.0 to +25.0) | 0.148 |
| gate vs instruction | 5 / 13 / 2 | +10.0 pts (−1.7 to +23.3) | 0.219 |
| medium vs gate | 6 / 10 / 4 | +3.3 pts (−11.7 to +18.3) | 0.836 |

As the design warned, 20 tasks can detect a gain of about 15 points, not 10.

### Cost and time

| arm | mean tokens | $ per verified pass | vs none | median seconds |
| --- | --- | --- | --- | --- |
| A none | 0.44M | 0.026 | 1.0 | 52 |
| B instruction | 1.33M | 0.063 | 2.4 | 116 |
| C skill | 1.77M | 0.079 | 3.0 | 137 |
| D revised skill | 1.78M | 0.075 | 2.9 | 134 |
| E medium effort | 0.88M | 0.039 | 1.5 | 94 |
| F gate | 1.67M | 0.066 | 2.5 | 220 |

- The skill made each run about a quarter more expensive than the instruction alone (a third more tokens), for no more relevant tests.
- The gate's runs took longest, because each attempt to finish runs the check: a median of 88 seconds (at most 134) for the second check, which runs Maven twice. The first check, finding no test, took 1 to 3 seconds.

### The gate (arm F)

- Every run has its gate records: two checks each.
- **Blocked at the first attempt to finish: 60 of 60**, all for "no test of its own".
- **At the second check: 58 of 60 had a relevant test.** One left its test failing, and one wrote a test that also passed on the original code. Both were let through, as designed.
- **The gate's last verdict matched the grader's relevance check in 60 of 60.**
- **No run touched the gate's files.** Agents referred to the hook when sent back ("The repository hook requires a regression test of the API itself"), so they knew a check existed.
- **A relevant test did not make the change correct.** 11 runs passed the gate and failed the hidden tests.

## Checks on the runs

- **All 360 runs completed and were fully graded.** In every run, every hidden test ran. There were no build failures before the tests.
- **Every run has a relevance record.** No check error occurred.
- **Only C and D read the skill,** in all of their runs (60 and 60). No other arm had it.
- **No run saw the hidden tests.** No command touched the experiments folder or a `hidden/` path.
- **The relevance check was validated before the runs** on explicit-skills' 27 test-writing runs (README, "Before the runs"), and spot-checked here: TAXRATE's instruction run 2, for example, posts invalid tax rates through `TestRestTemplate` and expects a 400. That fails on the original code, which accepts them.

## Exploratory analysis, added after the results

These were not part of the preregistered analysis.

- **After being sent back, 20 of 60 gated runs changed the code itself, not only tests.** 14 of those 20 passed. In the other 40, the agent only added a test; 33 passed. This was found from the transcripts: the block shows as two consecutive agent messages, and in all 60 runs the second one talks about the test or the hook. It suggests that writing the test after the fix sometimes exposed a gap in the fix. It cannot show the runs would have failed without it.
- **The gate's order differs from the instruction's.** Gated agents fixed first, unprompted, as in arm A, and wrote the test only when sent back. Instructed agents knew about the test from the start. Whether this order explains the gate's higher pass rate is a question for a later experiment; this one cannot settle it.
- **Runs with a relevant test passed more often** in every arm (B 41/56, C 40/52, D 43/54, F 47/58, against 1 of 20 without one, in total). This is not causal: an agent that cannot get its own test to pass has usually not solved the task.
- **The two neighbour-break tasks** (BOXVIS, REVEDIT) got relevant tests in every run of the asked or gated arms, except D's three REVEDIT runs and two of C's. Medium effort passed 5 of their 6 runs; every other arm passed 0 or 1. A test of the change does not catch a break elsewhere.

## Across the last five experiments

| intervention (Codex, low effort unless stated) | experiment | runs passed vs control | cost per correct change vs control |
| --- | --- | --- | --- |
| Superpowers skill pack | skills-tasks, verify-vs-skills | 24 vs 24 of 32; 37 vs 36 of 60 | about 2.4 to 2.5 times |
| A one-paragraph instruction to verify | verify-vs-skills | 39 vs 36 of 60 | 1.5 times |
| Repository guidance, left to discover | repo-skills; explicit-skills | 40 vs 38; 39 vs 37 of 60 | 1.2 to 1.3 times |
| Repository guidance, agent told to use it | explicit-skills | 42 and 43 vs 37 of 60 | 1.8 to 2.0 times |
| An instruction to write a focused API test | this one | 41 vs 40 of 60 | 2.4 times |
| The same, plus the verification skill | this one | 41 and 43 vs 40 of 60 | 2.9 to 3.0 times |
| A Stop-hook gate that requires a relevant test | this one | 47 vs 40 of 60 | 2.5 times |
| Medium reasoning effort, nothing else | verify-vs-skills; this one | 49 vs 36; 49 vs 40 of 60 (both significant) | 1.4 to 1.5 times |

Across five experiments, medium effort is the only intervention with a measurable gain in correct changes, and it is among the cheapest. In this one, the instruction reliably changed what the agent did. The gate changed it just as reliably, and came closest to medium effort on correctness.

## How far the result goes

- **One repository, one agent, one model, one verification skill**, revised by me. I know the tasks; the revision only reorders the original.
- **The instruction already said what the skill says.** Both ask for a focused test that fails without the change. A skill that carries knowledge the instruction lacks might add more. In this repository, the skill's main extra knowledge is how to run tests without starting the application. In arm B, without the skill, no run tried to start the application, and every run ran its tests.
- **E and F ran in their own trial files**, alongside A to D, not interleaved with them.
- **The gate was visible.** The agent could have read or changed its files, and none did.
- **Low effort only**, except arm E. The gate was not tried at medium effort.
- **Few neighbour-break tasks.** Only 2.
- **Selection.** The tasks were selected in verify-vs-skills on its arm A's runs.
- **The relevance check shows that a test tells the change from the original,** not that it tests what the task asked for.

## What changed from the design

Nothing in the design, hypotheses or analysis. One change to export: `scripts/export.sh` now also gzips the relevance check's Maven logs, which halved the size of the results. The analysis was re-run on the exported runs, and its output is identical. The checks and exploratory analysis above were added after the results.

## Reproducing

```
python3 -I scripts/make_trial.py && scripts/localize.sh
scripts/make_gate_home.sh ~/code/benchmark/skills-impact-work
trialrig run trial.local.toml --out <dir> --agent codex --parallel 3
trialrig run trial-medium.local.toml --out <dir-e> --agent codex
trialrig run trial-gate.local.toml --out <dir-f> --agent codex
scripts/export.sh <dir> stage1; scripts/export.sh <dir-e> stage1-medium; scripts/export.sh <dir-f> stage1-gate
python3 -I scripts/analyse.py results/stage1/runs results/stage1-medium/runs results/stage1-gate/runs > results/analysis.md
```
