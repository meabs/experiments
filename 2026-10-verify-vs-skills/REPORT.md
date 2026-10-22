# Verification, skills or effort? (Codex): report

Run on 2026-10-22. The design, hypotheses and selection rule are in [README.md](README.md), written before the measured runs, with every later change in its amendment log. The raw runs are in [results/stage1-low](results/stage1-low/) (arms A to C) and [results/stage1-medium](results/stage1-medium/) (arm D). The analysis is in [results/analysis.md](results/analysis.md), produced by `scripts/analyse.py`. The rig's own summaries are in [results/report-low.md](results/report-low.md) and [results/report-medium.md](results/report-medium.md).

## Summary

- **More reasoning effort was the only thing that measurably helped.**
  - Codex at medium effort, with no skills and no instruction, passed 49 of 60 runs, against 36 of 60 at low effort.
  - It was better on 9 tasks and worse on 1: +21.7 points (95% CI +5.0 to +36.7), Holm p = 0.041.
- **The instruction to verify did not measurably help.**
  - It passed 39 of 60 runs: 5 tasks better, 4 worse, +5.0 points (−10.0 to +20.0), Holm p = 0.67.
  - It used 1.87 times the control's tokens.
- **Superpowers did not help either, for the second time.**
  - It passed 37 of 60 runs, about the same as the control (+1.7 points, Holm p = 0.67), at 3.13 times the tokens.
  - In skills-tasks it also passed the same number as the control, at 3.07 times the tokens.
- **Medium effort was also the cheapest way to get a correct change, after doing nothing.**

  | arm | $ per verified pass |
  | --- | --- |
  | A none (low) | 0.028 |
  | D medium | 0.040 |
  | B verify | 0.042 |
  | C superpowers | 0.070 |

  The control is cheapest per pass because its runs are cheap, not because it passes more.
- **The instruction changed what the agent tried, not what it achieved.**
  - In 47 of 60 runs, the verify arm tried to start the application. No other arm did so even once.
  - In this repository, the application does not start outside its test harness: it needs a `database.properties` file the checkout does not have. Only 3 runs got as far as calling it.
  - The instruction also offered a fallback: "write or run a test that starts it". Only 5 runs wrote a test that calls the API.
- **Nobody fixed the neighbour-break task the design was built around.**
  - `REVEDIT` failed all 12 runs in every arm. In 9 of them, creating a review broke while fixing review editing.
  - The instruction to check every other caller of shared code did not reduce this. Runs that broke a neighbouring feature: verify 5, control 3 (H5, p = 1.0).
- **Failed runs still said they had worked.** In 78 of 79 failed runs across all arms, the agent's final claim said its change passed. This includes 20 of 21 in the verify arm, even though the instruction asked it to say plainly what it could not check.

## Setup

| | |
| --- | --- |
| Agent | Codex `gpt-5.6-luna`, clean home, the same isolation as skills-tasks |
| Repository | shopizer at `6a4a0a6` (Java, Maven, JDK 21) |
| Arms | **A** `none`, low effort: the task prompt only. **B** `verify`, low effort: the prompt plus a one-paragraph instruction in `AGENTS.md` (below). **C** `superpowers`, low effort: the Superpowers pack, built exactly as in skills-tasks. **D** `medium`, medium effort: the prompt only |
| Tasks | 20, chosen from a pool of 28 by a rule fixed before calibration. 18 are runtime traps (the obvious change compiles but is wrong when the app runs) and 2 are neighbour breaks (the obvious change breaks another feature that shares the code) |
| Runs | 20 tasks × 4 arms × 3 = 240, all completed (status `ok`, no timeouts). Arm D ran as a second trial file at the same time, because the rig cannot set effort per arm |
| Grading | Hidden API-level JUnit tests the agent never saw, plus the full existing suite. A run passes only if every hidden test ran and passed and no other test failed |
| Spend | $7.14 at list prices for the 240 runs |

The instruction for arm B, in full:

> Before you say you are done, check your change against the running application, not only by compiling it or by running the existing unit tests. Start the application, or write or run a test that starts it, and call the endpoints your change affects with the requests a client would send. Then find every other caller of any shared code you changed (services, mappers, populators, error handlers) and check that those callers still behave as they did before. In your final reply, say exactly what you ran and what you saw, and say plainly if you could not check something.

## Results by task

Passes out of 3:

| task | kind | A none (low) | B verify (low) | C superpowers (low) | D medium |
| --- | --- | --- | --- | --- | --- |
| ADDR | R | 1 | 3 | 2 | 3 |
| AMBIG | R | 3 | 3 | 3 | 3 |
| AVAIL | R | 3 | 3 | 3 | 3 |
| BOXGET | R | 3 | 3 | 3 | 3 |
| BOXVIS | N | 0 | 1 | 1 | 2 |
| CARTCALC | R | 3 | 2 | 2 | 3 |
| CARTLAST | R | 2 | 2 | 0 | 3 |
| CATCOUNT | R | 1 | 1 | 0 | 3 |
| CATDUP | R | 3 | 3 | 3 | 3 |
| CONTENT | R | 3 | 2 | 2 | 3 |
| CUSTDUP | R | 3 | 2 | 3 | 3 |
| CUSTLOGIN | R | 2 | 3 | 3 | 3 |
| CUSTREVIEW | R | 1 | 1 | 0 | 3 |
| NOTFOUND | R | 1 | 3 | 2 | 3 |
| PAGE | R | 3 | 1 | 2 | 3 |
| REVEDIT | N | 0 | 0 | 0 | 0 |
| REVIEW | R | 3 | 3 | 3 | 1 |
| SUPERDEL | R | 1 | 3 | 3 | 2 |
| TAXRATE | R | 0 | 0 | 2 | 2 |
| USERERR | R | 0 | 0 | 0 | 0 |
| **total** | | **36/60** | **39/60** | **37/60** | **49/60** |

- Six tasks gave the same result in all four arms: `AMBIG`, `AVAIL`, `BOXGET` and `CATDUP` were passed by every run, and `REVEDIT` and `USERERR` were failed by every run. In practice, the arms are compared on the other 14 tasks.
- Medium effort was the only arm that passed `CATCOUNT`, `CUSTREVIEW` and `CARTLAST` every time. It was also the only arm to do worse than the control on `REVIEW`, where 2 of 3 runs broke the rating checks.
- The verify arm's gains (`ADDR`, `NOTFOUND`, `SUPERDEL`) and losses (`PAGE`, `CARTCALC`, `CONTENT`, `CUSTDUP`) are mostly one or two runs each.
- `TAXRATE` repeats skills-tasks: Superpowers passed 2 of 3 and the control none. The verify instruction did not help on it (0 of 3).

## Preregistered tests

The unit is the task. Each comparison uses the per-task difference in passes, with an exact one-sided sign-flip test over tasks. H1 to H3 are Holm-adjusted together. Effects are the mean per-task difference in pass rate, with a bootstrap interval over tasks.

| # | hypothesis | tasks better / same / worse | difference in pass rate (95% CI) | p | Holm p | result |
| --- | --- | --- | --- | --- | --- | --- |
| H1 | `verify` beats `none` | 5 / 11 / 4 | +5.0 pts (−10.0 to +20.0) | 0.336 | 0.672 | not supported |
| H2 | `medium` beats `none` | 9 / 10 / 1 | +21.7 pts (+5.0 to +36.7) | 0.014 | **0.041** | supported |
| H3 | `superpowers` beats `none` | 6 / 8 / 6 | +1.7 pts (−13.3 to +16.7) | 0.500 | 0.672 | not supported |

- **H4** (reported, not tested): the verify arm's cost per verified pass was 0.60 times Superpowers' (95% CI 0.47 to 0.73). Verify is cheaper per correct change than Superpowers, but neither beats the control on pass rate.
- **H5** (secondary): on the 2 neighbour-break tasks, the control broke the neighbouring feature in 3 runs and the verify arm in 5 (p = 1.0). Not supported, and with only 2 tasks it could hardly have been.

Secondary comparisons (two-sided, unadjusted):

| comparison | tasks better / same / worse | difference in pass rate (95% CI) | p |
| --- | --- | --- | --- |
| verify vs superpowers | 5 / 12 / 3 | +3.3 pts (−8.3 to +15.0) | 0.80 |
| verify vs medium | 2 / 9 / 9 | −16.7 pts (−31.7 to −1.7) | 0.075 |
| superpowers vs medium | 2 / 9 / 9 | −20.0 pts (−38.3 to −1.7) | 0.073 |

Medium effort was ahead of both B and C on 9 tasks and behind on 2, but these comparisons are not significant. Tasks were selected on arms A and D's calibration runs, which slightly favours D here (see "How far the result goes").

## Cost and process

| arm | mean tokens | $ per run | $ per verified pass | minutes per verified pass | median seconds | ran Maven tests | wrote tests | wrote an API-level test | test-file-first |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A none (low) | 0.41M | 0.017 | 0.028 | 1.4 | 48 | 3/60 | 0/60 | 0/60 | 0/60 |
| B verify (low) | 0.75M | 0.027 | 0.042 | 2.2 | 81 | 23/60 | 5/60 | 5/60 | 0/60 |
| C superpowers (low) | 1.29M | 0.043 | 0.070 | 3.1 | 112 | 48/60 | 43/60 | 16/60 | 40/60 |
| D medium | 0.89M | 0.033 | 0.040 | 2.0 | 96 | 37/60 | 1/60 | 1/60 | 0/60 |

- Medium effort ran Maven tests in 37 of 60 runs without being asked, against 3 of 60 for the same agent at low effort. It almost never wrote tests of its own (1 of 60), but it read the existing ones and ran them.
- Superpowers again did the most testing: it ran the suite in 48 runs, wrote tests in 43 and wrote the test first in 40. That did not turn into more correct changes.

## Exploratory analysis, added after the results

These checks were not part of the preregistered analysis. The measures were written after seeing the data, and are in the last section of [results/analysis.md](results/analysis.md).

**Did the verify arm really check against the running app?** Rarely.

| arm | tried to start the app | its output shows it started | called it successfully |
| --- | --- | --- | --- |
| A none (low) | 0/60 | 0 | 0 |
| B verify (low) | 47/60 | 2 | 3 |
| C superpowers (low) | 0/60 | 0 | 0 |
| D medium | 0/60 | 0 | 0 |

- A typical verify run ran `mvn spring-boot:run`. The start failed because the checkout has no `database.properties`, and the run moved on.
- The instruction named a second route: "write or run a test that starts it". Shopizer's integration tests do start the application (`ServicesTestSupport`, with an in-memory database). Only 5 verify runs wrote such a test, against 16 for Superpowers.
- So the experiment mostly measured an instruction that the agent could not carry out as it understood it. In a repository where the app starts with one command, the result could be different.

**Did the agents say what they had not checked?** All of them did, almost always, so this does not separate the arms.

- The agents' final line has a field for what they could not check. 231 of 240 runs filled it, in every arm (A 60, B 57, C 55, D 59).
- Yet failed runs still reported `"result": "passed"`: A 24 of 24, B 20 of 21, C 23 of 23, D 11 of 11.
- The verify arm did name the real gap more often. For example: "The application did not start on localhost:8080, so live endpoint behavior could not be checked." It still reported the change as passed.
- **A rig limitation.** The rig's claim parser keeps the field only when it is a list, and most agents wrote it as a string. So the rig's own report shows almost no notes for this trial. The counts above come from the raw final messages.

**The effort clue from skills-tasks holds up, in part.**

- At high effort in calibration, Codex passed 47 of 50 runs. That included `REVEDIT` (`HREVIEW` in skills-tasks).
- At medium effort, it passed 49 of 60 measured runs, but `REVEDIT` none of 3.
- So medium effort buys most of the gain, and the hardest neighbour break needs more than medium.

## What went wrong, by task

### REVEDIT: the fix broke creating a review

The task asks for editing a product review to work. The natural fix changes the populator that both editing and creating use.

- **The breakage.** In 9 of 12 runs, creating a review stopped working (`keepsCreatingReviewsAndTheirRating` failed). That includes all 3 runs at medium effort and all 3 verify runs.
- **The other failures.** The remaining 3 runs (all low effort, none or Superpowers) failed the edit tests themselves, or broke an existing test.
- **The verify instruction.** It names populators as shared code whose other callers must be checked. The runs did not do it in a way that caught this.

### USERERR: a lazy proxy hides the missing user

The task asks for the right error statuses from the user API. Every run in every arm failed the same test: updating or changing the password of a missing user must give 404.

- The service's `getById` returns a lazy proxy, not null. The obvious "if null, 404" check never fires, and the request fails later with a 500.
- Seeing this needs a request against a missing id, which no run made.

### BOXVIS: hiding boxes from shoppers hid them from staff

`BOXVIS` is the second neighbour-break task: hidden content boxes must not show in the shop, but must still show in the back office.

- Medium effort passed 2 of 3, verify 1 and Superpowers 1. The control passed none.
- Five of the failed runs broke the back-office list.

### The others

- **`CATCOUNT`** (category product counts must include subcategories): the low-effort arms failed 7 of 9 runs. Medium effort passed all 3.
- **`CUSTREVIEW`** (editing a customer review): low-effort runs usually missed the missing-review case, a lazy proxy again, which should give 404. Medium effort passed all 3.
- **`REVIEW`** at medium effort: 2 of 3 runs failed the rating checks and the duplicate-review conflict, which every low-effort run passed. This is the only task where medium did worse than the control.

## How far the result goes

- **One repository, one agent, one model.** Claude wrote the tasks, hidden tests and patches, and they are committed for review.
- **The verify instruction met an app that does not start outside its tests.** This is real for many projects, but it means the experiment tested the instruction as Codex understood it, here. It does not test what checking against a running app is worth when that is easy.
- **Only 2 neighbour-break tasks.** Two others were too easy and were not kept, so H5 had almost no power.
- **Selection favours arms A and D.** Tasks were selected on their calibration runs. Through regression to the mean, this makes H1 and H3 conservative. It also helps D in the comparisons of D with B and C.
- **Arm D sits close to the ceiling.** The gate meant to stop this did not pass (see below). Medium effort passed 49 of 60 runs, which leaves little room to show anything beating it.
- **H2 is significant only just.** Holm p = 0.041 over 20 tasks, and 10 of the tasks did not differ.

## What changed from the design

All changes are in the README's amendment log with their dates. The main ones:

- **Arm D moved from high to medium effort before any measured run.** High effort passed 47 of 50 calibration runs, at the ceiling.
- **The gate did not pass, twice.** It required that at least 8 kept tasks be hard for arm D, and only 7 were.
  - Three tasks were added after the first failure (`BOXVIS`, `CUSTREVIEW`, `USERACTIVE`), and the gate still failed.
  - The runs went ahead at the user's decision, recorded before any measured run.
- **The pool grew from 25 to 28**, and 2 of the 3 original neighbour-break tasks were not kept.
- **Measures added after the results:**
  - whether the app started;
  - stated caveats read from the raw messages.

  Both are labelled exploratory.

## Suggested next step

Three follow-ups would separate the open questions:

- **Make "check it against the running app" possible.** Give the verify arm a one-command way to start the app (a test profile, or a documented `mvn` line with an in-memory database), and repeat B against A. This tests the instruction as intended, not the instruction against a missing config file.
- **Effort against cost, on the same tasks.** Low, medium and high effort, no skills. The open question is where the cost per correct change bottoms out, since medium already beat the packs on both pass rate and cost.
- **More neighbour-break tasks with prompts that do not name the neighbour.** `REVEDIT` defeated every arm below high effort, and that kind of failure is the one most likely to reach users.

## Reproducing

```
scripts/build_arms.sh                       # rebuild the Superpowers arm from its pinned commit
scripts/localize.sh                         # write trial.local.toml and trial-medium.local.toml for your home folder
trialrig run trial.local.toml --out <low> --agent codex          # arms A to C
trialrig run trial-medium.local.toml --out <medium> --agent codex  # arm D
scripts/export.sh <low> stage1-low
scripts/export.sh <medium> stage1-medium
python3 -I scripts/analyse.py results/stage1-low/runs results/stage1-medium/runs > results/analysis.md
```

`scripts/validate.py <ID> --full` re-checks each task:

- the hidden tests fail on the start, and every `keeps…` test passes on it;
- every hidden test passes with the reference, and so does the full suite;
- for neighbour-break tasks, the naive patch breaks a `keeps…` test while the existing suite stays green.
