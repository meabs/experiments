# Explicitly called skills (Codex): report

Run on 2026-10-22. The design and hypotheses are in [README.md](README.md), written before any run. Arm D was added by amendment while the main trial was running, before any result was looked at. The guidance is in [arms/guidance](arms/guidance/), byte-identical to repo-skills'. Arm D's version, with one added `AGENTS.md` entry, is in [arms/guidance-agentsmd](arms/guidance-agentsmd/). The raw runs are in [results/stage1](results/stage1/) (arms A to C) and [results/stage1-agentsmd](results/stage1-agentsmd/) (arm D). The analysis is in [results/analysis.md](results/analysis.md), from `scripts/analyse.py`. The rig's summaries are in [results/report.md](results/report.md) and [results/report-agentsmd.md](results/report-agentsmd.md).

## What is new here: the agent is told to use the skills

In [repo-skills](../2026-10-repo-skills/), the skills sat in the repository for the agent to find. It found two of them every time, but opened `verify-api`, the skill on checking a change through the API, in only 8 of 60 runs.

**This experiment tells the agent to use them.** The guidance is the same, byte for byte. Two arms add an instruction:

- **C, in the prompt.** The prompt starts by naming each skill and when to use it, including `verify-api` before finishing.
- **D, in `AGENTS.md`.** One entry at the end tells the agent to follow `verify-api` before it says it is done. A team would write this once, rather than a user writing it for each task.

## Summary

- **Reading is not doing.** This is the main result.
  - Told to use the skills, in the prompt or in `AGENTS.md`, the agent opened `verify-api` in 60 of 60 runs. Left to discover them, it opened it in 3 of 60.
  - The skill says to write a focused integration test for the change. A test of that kind was detected in the change of only 15 runs in C and 10 in D (from the diff: an added test using `TestRestTemplate`, `ServicesTestSupport` or `MockMvc`; not checked by hand).
  - Most runs ran the skill's first example instead: `ActuatorTest`, a smoke test that only checks the application starts and answers a health ping. It ran in 49 C runs and 47 D runs. In 23 C runs and 37 D runs, it was the only test the agent ran.
  - So the agent did not ignore the skill. It took the action in it that looked like verification and was easiest, rather than the one that checks the change.
- **The pass rate rose a little, but not measurably.**

  | arm | passed |
  | --- | --- |
  | A no guidance | 37/60 |
  | B guidance to discover | 39/60 |
  | C told in the prompt | 42/60 |
  | D told in `AGENTS.md` | 43/60 |

  - Telling the agent added 8 to 10 points over no guidance, and 5 to 7 over discovery.
  - None of the four tests is significant (Holm-adjusted p 0.33 to 0.41). H1 to H4 are not supported.
- **The prompt and `AGENTS.md` gave similar results.**
  - Both got the verification skill read in every run. The pass rates were similar, 42 and 43 of 60 (p = 1.0), but the experiment is too small to show whether placement matters.
  - The two instructions also differed in content: the prompt named all three skills, the `AGENTS.md` entry only `verify-api`. So this is not a pure test of placement.
  - The `AGENTS.md` entry was slightly cheaper.
- **It cost about twice as much per correct change.**
  - Cost per verified pass, against no guidance: C 1.98 times (95% CI 1.54 to 2.41); D 1.77 times (1.34 to 2.24).
  - Discovery cost 1.22 times.
  - Runs took twice as long: a median of about 115 seconds, against 53.
- **Failed runs still said they had worked.** All 79 failed runs, in all four arms.

## Setup

| | |
| --- | --- |
| Agent | Codex `gpt-5.6-luna`, reasoning effort low, clean home, the same isolation as before |
| Repository | shopizer at `6a4a0a6` (Java, Maven, JDK 21), offline |
| Guidance | repo-skills' agent-written `AGENTS.md` and three skills (`safe-change`, `build-test`, `verify-api`), unedited |
| Tasks | The 20 tasks of verify-vs-skills and repo-skills, unchanged: 18 runtime traps and 2 neighbour breaks |
| Runs | 20 tasks × 4 arms × 3 = 240, all completed (status `ok`, no timeouts). A to C ran in one trial file; D ran alongside in a second, started later |
| Grading | Hidden API-level JUnit tests the agent never saw, plus the full existing suite. A run passes only if every hidden test passes and no other test fails |
| Spend | $6.70 at list prices |

### The arms

| Arm | What the agent gets |
| --- | --- |
| A `none` | The task prompt only |
| B `discover` | The prompt, plus the guidance in the repository, left to discover (repeats repo-skills' arm B) |
| C `explicit` | The guidance, and the prompt starts with the instruction below |
| D `agentsmd` | The guidance, with one entry added to the end of `AGENTS.md`, below. The prompt is the task only |

Arm C's instruction, placed before the task:

> Use this repository's skills in .agents/skills for this task:
> 1. Before you change any code, read and follow .agents/skills/safe-change/SKILL.md.
> 2. To build and run tests, follow .agents/skills/build-test/SKILL.md.
> 3. Before you say you are done, read and follow .agents/skills/verify-api/SKILL.md, and check your change through the API as it says.
>
> The task:

Arm D's `AGENTS.md` entry:

> ## Before you finish
>
> Before you say you are done, read and follow `.agents/skills/verify-api/SKILL.md`, and check your change through the API as it says.

### What `verify-api` says

- Standalone startup does not work here. Use a `@SpringBootTest` integration test with `TestRestTemplate`.
- `ActuatorTest` shows the route works. The skill gives the command that runs it, as "the existing end-to-end smoke test".
- "For an API change, add or update a focused JUnit 4 integration test", calling the endpoint as a client would, and asserting both the status and the body.

## Results by task

Passes out of 3:

| task | kind | A none | B discover | C prompt | D `AGENTS.md` |
| --- | --- | --- | --- | --- | --- |
| ADDR | R | 3 | 3 | 3 | 3 |
| AMBIG | R | 3 | 3 | 3 | 3 |
| AVAIL | R | 3 | 2 | 3 | 3 |
| BOXGET | R | 3 | 3 | 3 | 3 |
| BOXVIS | N | 0 | 0 | 1 | 1 |
| CARTCALC | R | 3 | 3 | 3 | 3 |
| CARTLAST | R | 1 | 1 | 1 | 0 |
| CATCOUNT | R | 1 | 2 | 1 | 1 |
| CATDUP | R | 3 | 3 | 3 | 3 |
| CONTENT | R | 2 | 3 | 3 | 3 |
| CUSTDUP | R | 3 | 3 | 2 | 3 |
| CUSTLOGIN | R | 3 | 3 | 3 | 3 |
| CUSTREVIEW | R | 2 | 0 | 0 | 0 |
| NOTFOUND | R | 0 | 1 | 1 | 2 |
| PAGE | R | 3 | 3 | 3 | 3 |
| REVEDIT | N | 0 | 0 | 0 | 0 |
| REVIEW | R | 3 | 3 | 3 | 3 |
| SUPERDEL | R | 1 | 1 | 3 | 3 |
| TAXRATE | R | 0 | 2 | 3 | 3 |
| USERERR | R | 0 | 0 | 0 | 0 |
| **total** | | **37/60** | **39/60** | **42/60** | **43/60** |

- **Most tasks did not move.** 13 tasks came out the same in A and C, and 13 in A and D.
- **The gains came from a few tasks.**
  - `SUPERDEL` went from 1 of 3 to 3 of 3 in both told arms.
  - `TAXRATE` went from 0 (A) and 2 (B) to 3 in both told arms.
  - `NOTFOUND` and `BOXVIS` each gained a run or two.
- **One task went the other way.** `CUSTREVIEW` passed 2 of 3 with no guidance, and 0 in every arm with guidance. In repo-skills, the guidance arm passed it 2 of 3, so this is likely noise.
- **The baselines are stable.** A and B repeat repo-skills' two arms: 37 and 39 of 60 here, against 38 and 40 there.

## Preregistered tests

The unit is the task. The test is an exact one-sided sign-flip test over tasks, on the per-task difference in passes. The effect is the mean per-task difference in pass rate, with a bootstrap interval over tasks. H1 and H2 are Holm-adjusted together; H3 and H4, added by amendment, are adjusted as their own pair.

| hypothesis | tasks better / same / worse | difference in pass rate (95% CI) | p | Holm p | result |
| --- | --- | --- | --- | --- | --- |
| H1: C (prompt) beats none | 5 / 13 / 2 | +8.3 pts (−5.0 to +23.3) | 0.20 | 0.41 | not supported |
| H2: C (prompt) beats discover | 4 / 14 / 2 | +5.0 pts (−3.3 to +15.0) | 0.27 | 0.41 | not supported |
| H3: D (`AGENTS.md`) beats none | 5 / 13 / 2 | +10.0 pts (−5.0 to +26.7) | 0.16 | 0.33 | not supported |
| H4: D (`AGENTS.md`) beats discover | 5 / 13 / 2 | +6.7 pts (−3.3 to +16.7) | 0.18 | 0.33 | not supported |

Secondary, two-sided and unadjusted:

- C against D: 1 / 17 / 2, −1.7 pts (−6.7 to +3.3), p = 1.0.
- B against none: 4 / 14 / 2, +3.3 pts (−8.3 to +15.0), p = 0.78. This repeats repo-skills' result.

The design said a gain of about 15 to 20 points was detectable. The point estimates are 8 to 10 points, and the intervals reach +23 and +27. A real gain of that size could be there, but this experiment is too small to show it.

## Cost and process

| arm | mean tokens | $ per verified pass | vs none | median seconds | read `verify-api` | ran Maven tests | API-level test detected in the change | tried to start the app |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A none | 0.40M | 0.028 | 1 | 53 | 0/60 | 6/60 | 0/60 | 0/60 |
| B discover | 0.56M | 0.034 | 1.22 | 73 | 3/60 | 16/60 | 0/60 | 0/60 |
| C prompt | 1.10M | 0.054 | 1.98 | 113 | 60/60 | 60/60 | 15/60 | 0/60 |
| D `AGENTS.md` | 0.99M | 0.049 | 1.77 | 117 | 60/60 | 59/60 | 10/60 | 0/60 |

- **Read, then took the shortcut.**
  - Told to follow `verify-api`, the agent ran a test in almost every run.
  - Most often it ran the skill's example, `ActuatorTest`, which checks only that the application starts and answers a health ping. It does not touch the change.
  - Its end-of-run claims said so: for example, "the specific customer address PATCH/GET flow was not covered by an existing integration test".
- **Writing a test was the step that was skipped.** An API-level test was detected in the change of only 15 C runs and 10 D runs, even though the skill says to add one. The count comes from the diff (an added line using `TestRestTemplate`, `ServicesTestSupport` or `MockMvc`); it does not show that the test exercised the change.
- **Neighbour breaks.** Runs with a broken neighbouring feature, on the 2 neighbour-break tasks: none 4, discover 5, C 5, D 4. Being told to use `safe-change`, which says to check every caller of shared code, did not prevent them.
- **False success claims.** Every failed run claimed success: none 23 of 23, discover 21 of 21, C 18 of 18, D 17 of 17.

## Checks on the runs

These were checked from the raw event streams before the results were written up. The clones are deleted after each run, so the streams are the record.

- **The guidance reached B, C and D, and not A.**
  - In every run in B, C and D, the agent ran a command that read a skill file.
  - No A run's event stream mentions `AGENTS.md` or `.agents`, and no run anywhere found `.agents` missing.
- **The skills were really read.**

  | skill | B | C | D |
  | --- | --- | --- | --- |
  | `safe-change` | 60 | 60 | 60 |
  | `build-test` | 58 | 60 | 58 |
  | `verify-api` | 3 | 60 | 60 |

  The skill text is visible in the logged output in 60 C runs and 58 D runs. In the rest, the stream kept only part of a long output.
- **The `AGENTS.md` entry was in effect.**
  - D was not told anything in the prompt, yet it opened `verify-api` in 60 of 60 runs, against 3 of 60 in B, whose `AGENTS.md` lacks only the entry.
  - Codex loads `AGENTS.md` itself, so it never shows up as a read.
- **Grading was complete.**
  - All 240 runs have a grading summary.
  - In 239, every hidden test ran. In the remaining run (C, `CUSTREVIEW`, run 3), the agent left code that does not compile, so the build failed before any test ran. It counts as a fail, as it would for any change that does not compile.
- **No run saw the hidden tests.**
  - No command touched the experiments folder or a `hidden/` path.
  - The one command the scan flagged read a skill inside the agent's own clone.

## Later check: were the detected tests real tests of the change?

Added after the report, while preparing [test-skill](../2026-10-test-skill/), and checked automatically rather than by hand. Each of the 27 runs that changed a test file was rebuilt from its saved diff. The agent's own tests were then run with its change, and again on the original code.

- **All 27 have a relevant test.** Every test passes with the change, and at least one fails on the original code.
- **The count from the diff slightly undercounted.** It found 15 (prompt) and 10 (`AGENTS.md`); the check finds 16 and 11. One run per arm, both on CARTCALC, wrote a relevant test the pattern missed. Every test it did find was relevant.
- So the main result stands, with slightly firmer numbers: told to follow the skill, the agent wrote a real test of its change in 16 and 11 of 60 runs.

The method and results are in test-skill's README ("Before the runs") and [`results/retro-explicit-skills`](../2026-10-test-skill/results/retro-explicit-skills/).

## Exploratory analysis, added after the results

These were not part of the preregistered analysis.

- **Runs with an API-level test detected in the change passed more often.** In C: 13 of 15, against 29 of 45. In D: 9 of 10, against 34 of 50. This is not causal: an agent may write a test more readily when it understands the task.
- **Runs that ran only the smoke test** passed 14 of 23 in C and 24 of 37 in D, a little below each arm overall (42 and 43 of 60).
- **By kind of task.**
  - Runtime traps: none 37/54, discover 39/54, C 41/54, D 42/54.
  - Neighbour breaks: none 0/6, discover 0/6, C 1/6, D 1/6.

## Across the last four experiments

| intervention (Codex, low effort unless stated) | experiment | runs passed vs control | cost per correct change vs control |
| --- | --- | --- | --- |
| Superpowers skill pack | skills-tasks, verify-vs-skills | 24 vs 24 of 32; 37 vs 36 of 60 | about 2.4 to 2.5 times |
| A one-paragraph instruction to verify | verify-vs-skills | 39 vs 36 of 60 | 1.5 times |
| Repository guidance, left to discover | repo-skills; this one | 40 vs 38; 39 vs 37 of 60 | 1.2 to 1.3 times |
| Repository guidance, agent told in the prompt | this one | 42 vs 37 of 60 | 2.0 times |
| Repository guidance, agent told in `AGENTS.md` | this one | 43 vs 37 of 60 | 1.8 times |
| Medium reasoning effort, nothing else | verify-vs-skills | 49 vs 36 of 60 (significant) | 1.4 times |

Telling the agent to use the guidance gave the largest gain of any text-based intervention so far, but it is still not measurable, and it cost about twice as much per correct change. Medium effort, in an earlier experiment, gained more for less.

## How far the result goes

- **One repository, one agent, one model, one set of guidance**, written by an agent.
- **The skill's example invited the shortcut.** `verify-api` puts the smoke-test command first, and a focused test second. A skill that only gave the route to a focused test might be followed more fully. This experiment cannot say.
- **The instruction adds emphasis, not only access.** C and D add text about checking before finishing. Their gain could come from that emphasis as much as from the skills.
- **D ran later.** Arm D ran in a second trial file, started while A to C were running, so it covers later hours.
- **Low effort only.**
- **Few neighbour-break tasks.** Only 2.
- **Selection.** The tasks were selected in verify-vs-skills on arm A's runs, which favours arm A slightly.

## What changed from the design

Arm D and its hypotheses (H3, H4) were added by amendment while the main trial was running, before any result was looked at. They are adjusted separately, so H1, H2 and their adjustment are as preregistered. Nothing else changed. The checks and exploratory analysis above were added after the results.

## Reproducing

```
python3 -I scripts/make_trial.py && scripts/localize.sh
trialrig run trial.local.toml --out <dir> --agent codex
trialrig run trial-agentsmd.local.toml --out <dir-d> --agent codex
scripts/export.sh <dir> stage1
scripts/export.sh <dir-d> stage1-agentsmd
python3 -I scripts/analyse.py results/stage1/runs results/stage1-agentsmd/runs > results/analysis.md
```
