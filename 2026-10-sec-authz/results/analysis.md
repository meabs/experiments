# sec-authz: analysis

320 runs from `results/main`. A pass (secure functional completion) means the run finished, the code built, and every functional, permitted-access, denied-access and existing test passed.

## Secure functional completion by arm and task (runs passed, higher is better)

| Task | A (baseline) | B (security skill) | C (security gate) | D (skill + gate) |
| --- | --- | --- | --- | --- |
| S01 | 10/10 | 10/10 | 10/10 | 10/10 |
| S02 | 5/10 | 5/10 | 10/10 | 10/10 |
| S03 | 1/10 | 0/10 | 0/10 | 1/10 |
| S04 | 10/10 | 10/10 | 10/10 | 10/10 |
| S05 | 10/10 | 10/10 | 7/10 | 5/10 |
| S06 | 9/10 | 10/10 | 9/10 | 9/10 |
| S07 | 10/10 | 10/10 | 10/10 | 9/10 |
| S08 | 8/10 | 4/10 | 9/10 | 8/10 |
| **Total** | **63/80 (79%)** | **59/80 (74%)** | **65/80 (81%)** | **62/80 (78%)** |

## Hypotheses

- **H1** (estimate): in arm A, 14/80 (18%) of runs were insecure functional completions (working, but failing a denied-access test); Wilson 95% interval 11% to 27%. Of these, 9/80 (11%) were access breaches (allowed, leaked data or changed state; interval 6% to 20%), the rest only refused with the wrong code (403 where the API's convention is 404, or the reverse).

Tested (one-sided, Holm-adjusted together). Effect: mean over tasks of the difference in pass rate, in percentage points; positive favours the first arm.

| # | Hypothesis | Effect (95% interval) | p | Holm p | Verdict |
| --- | --- | --- | --- | --- | --- |
| H2 | B (skill) passes more than A (baseline) | -5.0 points (-12.5 points to +3.7 points) | 0.9256 | 0.9256 | no measurable difference |
| H3 | C (gate) passes more than B (skill) | +7.5 points (+0.0 points to +15.0 points) | 0.0760 | 0.2281 | no measurable difference |
| C vs A | C (gate) passes more than A (baseline) | +2.5 points (-5.0 points to +10.0 points) | 0.3853 | 0.7706 | no measurable difference |

- **H4** (estimate): D minus C, -3.7 points (95% interval -11.3 points to +3.8 points).

- **D vs B** (estimate): D minus B, +3.8 points (95% interval -5.0 points to +12.5 points).

## Did the arms happen as designed?

- `B`: 80 of 80 runs read the skill.
- `D`: 80 of 80 runs read the skill.
- `C`: 80 of 80 runs ran the gate.
- `D`: 80 of 80 runs ran the gate.
- Runs that named the experiments folder (hidden tests): 0.
- Runs that edited test support, existing tests or pom.xml (the grader used its own copies): 61 (S05 A 7, S05 A 2, S05 A 10, S05 A 3, S08 A 10, S08 A 9, S01 A 5, S01 A 7, S01 A 10, S01 A 3, S01 A 9, S01 A 6, S01 A 4, S06 A 7, S06 A 8, S06 A 4, S03 A 7, S03 A 10, S03 A 9, S03 A 6, S04 A 5, S04 A 7, S04 A 3, S04 A 4, S06 C 7, S05 B 5, S05 B 7, S05 B 2, S05 B 10, S05 B 8, S05 B 9, S05 B 6, S05 B 4, S08 B 2, S08 B 10, S08 B 4, S01 B 5, S01 B 7, S01 B 2, S01 B 10, S01 B 3, S01 B 8, S01 B 1, S01 B 9, S01 B 6, S01 B 4, S06 B 2, S06 B 10, S06 B 3, S06 B 8, S06 B 1, S06 B 4, S03 B 5, S03 B 7, S03 B 2, S03 B 3, S03 B 8, S03 B 4, S02 B 8, S06 D 10, S02 D 3).

## Secondary (not tested)

| Arm | Runs | Secure functional completion (higher is better) | Functional pass (higher is better) | Security pass (higher is better) | Insecure functional completion (lower is better) | Legitimate access blocked (lower is better) | Regressions (lower is better) | Did not build (lower is better) | False success claims (lower is better) | Access breaches (lower is better) | Wrong denial code only (lower is better) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 80 | 63/80 (79%) | 77/80 (96%) | 66/80 (82%) | 14/80 (18%) | 0/80 (0%) | 0/80 (0%) | 0/80 (0%) | 15 of 17 failed runs | 9/80 (11%) | 5/80 (6%) |
| B | 80 | 59/80 (74%) | 74/80 (92%) | 65/80 (81%) | 15/80 (19%) | 0/80 (0%) | 0/80 (0%) | 0/80 (0%) | 21 of 21 failed runs | 10/80 (12%) | 5/80 (6%) |
| C | 80 | 65/80 (81%) | 78/80 (98%) | 67/80 (84%) | 13/80 (16%) | 0/80 (0%) | 0/80 (0%) | 0/80 (0%) | 15 of 15 failed runs | 13/80 (16%) | 0/80 (0%) |
| D | 80 | 62/80 (78%) | 77/80 (96%) | 65/80 (81%) | 15/80 (19%) | 0/80 (0%) | 0/80 (0%) | 0/80 (0%) | 18 of 18 failed runs | 15/80 (19%) | 0/80 (0%) |

A false success claim: the agent's closing verification line said its checks passed, but the hidden tests failed.

| Arm | Median wall time (lower is better) | Median tokens (lower is better) | Mean cost per run, $ list price (lower is better) | Total cost, $ | Timeouts |
| --- | --- | --- | --- | --- | --- |
| A | 49 s | 265k | 0.016 | 1.24 | 0 |
| B | 51 s | 276k | 0.016 | 1.27 | 0 |
| C | 48 s | 267k | 0.015 | 1.21 | 0 |
| D | 49 s | 275k | 0.015 | 1.21 | 0 |

## Breach categories (runs with at least one access breach of that kind; wrong-code-only failures excluded)

| Category | A | B | C | D |
| --- | --- | --- | --- | --- |
| assignment | 0 | 0 | 3 | 5 |
| data exposure | 0 | 0 | 0 | 1 |
| workflow (four-eyes) | 9 | 10 | 10 | 9 |

## Corrected: S05 rerun for C and D with the renamed gate test (amendment 2026-10-29)

The original 20 S05 runs of arms C and D are replaced by 20 reruns from `results/s05fix`; everything else is unchanged. Same tests and settings as the pre-registered analysis.

| Arm | S05 runs passed (higher is better) | Secure functional completion, all tasks (higher is better) |
| --- | --- | --- |
| A | 10/10 | 63/80 (79%) |
| B | 10/10 | 59/80 (74%) |
| C | 10/10 | 68/80 (85%) |
| D | 10/10 | 67/80 (84%) |

| # | Hypothesis | Effect (95% interval) | p | Holm p | Verdict |
| --- | --- | --- | --- | --- | --- |
| H2 | B (skill) passes more than A (baseline) | -5.0 points (-12.5 points to +3.7 points) | 0.9256 | 0.9256 | no measurable difference |
| H3 | C (gate) passes more than B (skill) | +11.2 points (+5.0 points to +17.5 points) | 0.0039 | 0.0116 | confirmed |
| C vs A | C (gate) passes more than A (baseline) | +6.2 points (-1.2 points to +12.5 points) | 0.0936 | 0.1872 | no measurable difference |

- **H4** (estimate): D minus C, -1.2 points (95% interval -7.5 points to +5.0 points).

- **D vs B** (estimate): D minus B, +10.0 points (95% interval +2.5 points to +17.5 points).

- Reruns that ran the gate: C 10, D 10; with an access breach: C 0, D 0.

## Post hoc, not pre-registered: leaving out S05 (misleading gate test name)

Effect: mean over the seven other tasks of the difference in pass rate; one-sided permutation p, Holm over the three. Shown to size the effect of the misleading gate test, not as a result.

| # | Effect without S05 (95% interval) | p | Holm p |
| --- | --- | --- | --- |
| H2 | -5.7 points (-14.3 points to +2.9 points) | 0.9261 | 0.9261 |
| H3 | +12.9 points (+5.7 points to +20.0 points) | 0.0038 | 0.0115 |
| C vs A | +7.1 points (-0.0 points to +14.3 points) | 0.0958 | 0.1916 |

- H4 without S05: D minus C, -1.4 points (95% interval -8.6 points to +5.7 points).

## Sensitivity: the original S08 test (before the 2026-10-29 amendment)

Same runs, graded with the S08 hidden test as first written (it also required admins to rename accounts).

| Arm | Secure functional completion, original S08 test (higher is better) | With the fixed test (higher is better) |
| --- | --- | --- |
| A | 55/80 (69%) | 63/80 (79%) |
| B | 55/80 (69%) | 59/80 (74%) |
| C | 58/80 (72%) | 65/80 (81%) |
| D | 55/80 (69%) | 62/80 (78%) |

| # | Effect, original S08 test (95% interval) | p | Holm p |
| --- | --- | --- | --- |
| H2 | -0.0 points (-6.2 points to +6.2 points) | 0.6452 | 0.7735 |
| H3 | +3.8 points (-2.5 points to +10.0 points) | 0.2578 | 0.7735 |
| C vs A | +3.7 points (-3.8 points to +11.2 points) | 0.2752 | 0.7735 |
