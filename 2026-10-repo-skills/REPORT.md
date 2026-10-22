# Repository skills (Codex): report

Run on 2026-10-22. The design, hypothesis and generation brief are in [README.md](README.md), written before the guidance existed and before any run; later changes are in its amendment log. The guidance the agent used is in [arms/repo-skills](arms/repo-skills/), unedited, with its generation record in [generate/record](generate/record/). The raw runs are in [results/stage1](results/stage1/), the analysis is in [results/analysis.md](results/analysis.md) (from `scripts/analyse.py`), and the rig's summary is in [results/report.md](results/report.md).

## Summary

- **Repository guidance did not measurably raise the pass rate.**
  - With an agent-written `AGENTS.md` and three skills, Codex passed 40 of 60 runs, against 38 of 60 with none.
  - It was better on 5 tasks and worse on 5: +3.3 points (95% CI −8.3 to +16.7), one-sided p = 0.40.
  - H1 is not supported.
- **The guidance was read, but its verification skill mostly was not.**
  - Every run read the `build-test` and `safe-change` skills.
  - Only 8 of 60 opened `verify-api`, the skill that explains how to test a change through the running API.
- **The agent ran existing tests, but rarely wrote one for its own change.**
  - With guidance, it ran Maven tests in 26 of 60 runs (without: 5), usually a single existing integration test class.
  - Those classes start the application and call its API, but they test the old behaviour.
  - Only 2 of 60 runs wrote a test of their own.
- **It cost a little more.**
  - Mean tokens were 0.55M against 0.38M.
  - Cost per verified pass was 1.29 times the control's (95% CI 1.01 to 1.55): $0.033 against $0.026.
  - That is far less than Superpowers' 2.5 to 3 times in earlier experiments.
- **It did not prevent neighbour breaks.**
  - On `REVEDIT`, all 3 runs with guidance broke creating a review; none of the 3 without it did.
  - `safe-change` tells the agent to search every caller of shared code before changing it.
  - Across the 2 neighbour-break tasks: 5 runs with a broken neighbouring feature with guidance, 2 without.
- **Failed runs still said they had worked.** 42 of 42 failed runs, in both arms.

## Setup

| | |
| --- | --- |
| Agent | Codex `gpt-5.6-luna`, reasoning effort low, clean home, the same isolation as before |
| Repository | shopizer at `6a4a0a6` (Java, Maven, JDK 21), offline |
| Arms | **A** `none`: the task prompt only. **B** `repo-skills`: the prompt, plus the generated `AGENTS.md` at the repository root and three skills under `.agents/skills/` |
| Guidance | Written by Codex at high effort in one 3-minute run, from [a fixed brief](generate/brief.md), in a fresh clone with all of `~/code` (the tasks, earlier runs, notes) hidden from it. Kept unedited |
| Tasks | The 20 tasks of verify-vs-skills, unchanged: 18 runtime traps and 2 neighbour breaks |
| Runs | 20 tasks × 2 arms × 3 = 120, all completed (status `ok`, no timeouts) |
| Grading | Hidden API-level JUnit tests the agent never saw, plus the full existing suite. A run passes only if every hidden test passes and no other test fails |
| Spend | $2.30 at list prices for the 120 runs, plus about $0.11 for the generation run |

### What the guidance says

- **`AGENTS.md` (8 lines).** The modules, the build command, the command to run one test class, and which skill to use when.
- **`build-test`.**
  - Build offline, run the full suite, and run a single test class with `-pl sm-shop -am -Dtest=<Class> -DfailIfNoTests=false`.
  - Check `git status` after tests, because they write files.
- **`verify-api`.**
  - The application does not start on its own here, because `database.properties` exists only in the test resources.
  - Instead, write a `@SpringBootTest` integration test with `TestRestTemplate`, using `ServicesTestSupport` for the admin login, and call the endpoint as a client would.
  - This is the route the verify-vs-skills instruction needed, and its agent almost never found it.
- **`safe-change`.**
  - How a request flows: controller, facade, service, repository.
  - Which exception becomes which HTTP status in `RestErrorHandler`.
  - Search every caller of shared code before changing it.

One statement in it is inaccurate, and was recorded before the runs: `ServiceRuntimeException` becomes 400 only when it carries a cause; without one, the answer is 500. No passage describes the specific cause of any of the 20 tasks.

## Results by task

Passes out of 3:

| task | kind | A none | B repo skills |
| --- | --- | --- | --- |
| ADDR | R | 3 | 2 |
| AMBIG | R | 3 | 3 |
| AVAIL | R | 3 | 3 |
| BOXGET | R | 3 | 3 |
| BOXVIS | N | 1 | 0 |
| CARTCALC | R | 3 | 3 |
| CARTLAST | R | 3 | 2 |
| CATCOUNT | R | 1 | 2 |
| CATDUP | R | 3 | 3 |
| CONTENT | R | 2 | 3 |
| CUSTDUP | R | 3 | 3 |
| CUSTLOGIN | R | 3 | 2 |
| CUSTREVIEW | R | 0 | 2 |
| NOTFOUND | R | 1 | 2 |
| PAGE | R | 3 | 2 |
| REVEDIT | N | 0 | 0 |
| REVIEW | R | 3 | 3 |
| SUPERDEL | R | 0 | 2 |
| TAXRATE | R | 0 | 0 |
| USERERR | R | 0 | 0 |
| **total** | | **38/60** | **40/60** |

- **Same in both arms (10 tasks).**
  - Every run passed 7 tasks: `AMBIG`, `AVAIL`, `BOXGET`, `CARTCALC`, `CATDUP`, `CUSTDUP` and `REVIEW`.
  - Every run failed 3: `REVEDIT`, `TAXRATE` and `USERERR`.
- **Where the guidance gained.** Two tasks went from 0 to 2: `SUPERDEL` and `CUSTREVIEW`. Three more gained one run each: `CATCOUNT`, `NOTFOUND` and `CONTENT`.
- **Where it lost.** It lost one run each on `ADDR`, `BOXVIS`, `CARTLAST`, `CUSTLOGIN` and `PAGE`, all tasks the control passed every time or nearly so.
- **Arm A against verify-vs-skills.** Arm A was rerun here and passed 38 of 60. In verify-vs-skills, the same arm passed 36 of 60, so the baseline is stable.

## Preregistered test

The unit is the task. The test is an exact one-sided sign-flip test over tasks, on the per-task difference in passes. The effect is the mean per-task difference in pass rate, with a bootstrap interval over tasks.

| hypothesis | tasks better / same / worse | difference in pass rate (95% CI) | p | result |
| --- | --- | --- | --- | --- |
| H1: `repo-skills` beats `none` | 5 / 10 / 5 | +3.3 pts (−8.3 to +16.7) | 0.40 | not supported |

The design said that a gain of about 15 to 20 points was detectable. The interval's upper end is +16.7 points, so a benefit of up to that size cannot be ruled out.

## Cost and process

| arm | mean tokens | $ per run | $ per verified pass | median seconds | read a skill | ran Maven tests | wrote tests | wrote an API-level test | tried to start the app |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A none | 0.38M | 0.016 | 0.026 | 43 | 0/60 | 5/60 | 0/60 | 0/60 | 0/60 |
| B repo skills | 0.55M | 0.022 | 0.033 | 61 | 60/60 | 26/60 | 2/60 | 2/60 | 0/60 |

- **Which skills it read.**
  - In all 60 runs, the agent's first command printed `safe-change` and `build-test` (see "Checks on the runs").
  - Only 8 runs read `verify-api`.
  - `AGENTS.md` points to `verify-api` "for endpoint/client behavior", but at low effort that did not draw the agent in.
- **No one tried to start the application.** The skill said that route does not work here, so the 47 failed attempts of verify-vs-skills did not recur.
- **What tests it ran.** Of the 26 runs that ran tests, 24 ran one existing integration test class, most often `UserApiIntegrationTest` (11 runs). In all 26, at least one test command succeeded. Existing tests describe the behaviour before the change, so a green run here says little about the change itself.

## Checks on the runs

These were checked from the raw event streams, after the results, at the user's request. The clones are deleted after each run, so the streams are the record.

- **The guidance reached arm B, and only arm B.**
  - In all 60 arm B runs, the commands or their output show `AGENTS.md` or `.agents/`.
  - In arm A, none of the 60 runs shows either.
- **The skills were really read, not just named.**
  - In every arm B run, the first command printed `safe-change/SKILL.md` and `build-test/SKILL.md` with `sed`, and it exited 0. In 45 runs, the skill text is visible in the logged output.
  - In the other 15, the same command went on to run a code search, and the stream kept only part of a long output, or none of it. They still exited 0, and the commands were chained with `&&`, so a missing file would have stopped them with an error.
  - `verify-api` was read in 8 runs, with its text visible in all 8.
  - No arm A run read a skill.
- **`AGENTS.md` was in effect.** Arm B used the commands it gives; arm A almost never did.

  | command | arm B runs | arm A runs |
  | --- | --- | --- |
  | offline Maven (`mvn -o`) | 59 | 0 |
  | the single-class flag (`-DfailIfNoTests=false`) | 24 | 1 |

  Codex loads `AGENTS.md` itself, so it never shows up as a read.
- **Grading was complete.**
  - All 120 runs have a grading summary.
  - In every run, the number of hidden tests that ran equals the number expected.
- **Neither arm saw the hidden tests.** No run's event stream mentions the experiments folder, a `hidden/` path or a hidden test class name.

## Exploratory analysis, added after the results

These checks were not part of the preregistered analysis.

- **Did the right error mapping help on `SUPERDEL`?**
  - The task asks for deleting the super administrator to answer 400.
  - Both runs with guidance that passed threw an exception that `safe-change` maps to 400 (`RestApiException`, or `ServiceRuntimeException` with a message).
  - None of the three runs without guidance threw an exception mapped to 400. They threw `ResourceNotFoundException` and, in one run, `OperationNotAllowedException`, and all three failed the super administrator check.
  - This is a plausible mechanism, not proof.
- **Did the "search every caller" advice help on `REVEDIT`?** No.
  - All three runs with guidance broke review creation (`keepsCreatingReviewsAndTheirRating`).
  - The three without guidance did not break it, but failed the edit tests themselves.
  - Neither arm passed.
- **Arm B runs that wrote an API-level test** passed 2 of 2. Runs that did not passed 38 of 58. Two runs are far too few to read anything into.
- **Arm B runs that ran Maven tests** passed 19 of 26. Runs that did not passed 21 of 34. This is not causal: harder tasks may draw more checking.

## Across the last three experiments

| intervention (Codex, low effort unless stated) | experiment | runs passed vs control | cost per correct change vs control |
| --- | --- | --- | --- |
| Superpowers skill pack | skills-tasks, verify-vs-skills | 24 vs 24 of 32; 37 vs 36 of 60 | about 2.4 to 2.5 times |
| A one-paragraph instruction to verify | verify-vs-skills | 39 vs 36 of 60 | 1.5 times |
| Repository guidance written by an agent | repo-skills | 40 vs 38 of 60 | 1.3 times |
| Medium reasoning effort, nothing else | verify-vs-skills | 49 vs 36 of 60 (significant) | 1.4 times |

Only effort has made a measurable difference. Of the text-based interventions, repository guidance was the cheapest per correct change, but it did not produce more correct changes.

## How far the result goes

- **One repository, one agent, one model, one generated set of guidance.** A different generation run, or guidance a team refined over time, could do better.
- **Low effort only.** The agent read its guidance but did not follow its main verification advice. A more capable setting might use it more.
- **Few neighbour-break tasks.** Only 2, so the neighbour-break result is an observation, not a test.
- **Selection.** The tasks were selected in verify-vs-skills on arm A's runs, which favours arm A slightly here.

## What changed from the design

Nothing in the preregistered analysis changed. The amendment log records the generation run and the review of the guidance, both before any measured run. The exploratory checks above were added after the results.

## Suggested next step

The guidance told the agent how to verify, and the agent did not open that part. Two follow-ups would separate why:

- **Make verification part of the task, not an optional skill.** Put the one route that works (write a `@SpringBootTest` test of the changed endpoint, run it with the given command) in `AGENTS.md` as a required step, and repeat B against A. This tests whether following the advice helps, rather than whether the agent chooses to read it.
- **Guidance with more effort.** Repeat A and B at medium effort. This tests whether repository guidance adds anything once the agent thinks for longer.

## Reproducing

```
python3 -I scripts/make_trial.py && scripts/localize.sh
trialrig run trial.local.toml --out <dir> --agent codex       # uses the committed arms/repo-skills
scripts/export.sh <dir> stage1
python3 -I scripts/analyse.py results/stage1/runs > results/analysis.md
```

To generate a new set of guidance instead, run `trialrig run generate/generate.local.toml --out <gen> --agent codex` and copy `<gen>/runs/GENERATE/none/codex/1/generated/` to `arms/repo-skills/`.
