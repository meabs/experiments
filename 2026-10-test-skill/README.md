# Does a skill add anything to an instruction to test? (Codex)

**Draft design, written 2026-10-22. Not yet run.** Nothing below is fixed until it is committed as final; after that, changes go in the amendment log at the bottom.

## Why this follows explicit-skills

[2026-10-explicit-skills](../2026-10-explicit-skills/) told the agent to use the repository's skills. It then read the verification skill, `verify-api`, in every run (60 of 60, against 3 of 60 when left to find it). But it mostly did not do what the skill asks.

- The skill says to write a focused integration test of the change. A test of that kind was detected in only 15 and 10 of 60 runs.
- Most runs ran the skill's first example instead: `ActuatorTest`, a smoke test that only checks the application starts.
- The pass rate rose from 37 to 42 and 43 of 60, not significantly.

That leaves two open questions:

1. **Does the skill add anything beyond simply telling the agent to write the test?** The explicit-skills arms combined the skills with an instruction, so their effects cannot be separated.
2. **Was the shortcut caused by the skill's design?** The original skill gives the smoke-test command first, and the advice to write a focused test second.

This design came out of a review of explicit-skills: four arms (A to D) as the review proposed, plus a medium-effort arm (E) and a direct measure of whether the agent's test checks its change.

## Question

When the agent is told to write a focused API test of its change, does giving it the repository's verification skill raise the share of runs that write a test which really checks the change? Does a skill that puts the focused test first do better than the original?

## Agent and repository

- Codex `gpt-5.6-luna`, clean home, the same isolation as before. Low reasoning effort, except arm E.
- shopizer at `6a4a0a6` (Java, Maven, JDK 21), offline.

## Arms

| Arm | Name | What the agent gets |
| --- | --- | --- |
| A | `none` | The task prompt only |
| B | `instruction` | The prompt starts with an instruction to write and run a focused API test of the change ([`arms/instruction.md`](arms/instruction.md)). No skill |
| C | `skill` | The same instruction, plus a pointer to the skill ([`arms/instruction-skill.md`](arms/instruction-skill.md)), and the original `verify-api` skill, unedited ([`arms/skill-original`](arms/skill-original/)) |
| D | `skill-revised` | As C, with a revised `verify-api` that puts the focused test first ([`arms/skill-revised`](arms/skill-revised/)) |
| E | `medium` | The task prompt only, at medium reasoning effort |

The instruction for B:

> Before you say you are done, add a focused test that checks your change through the API, calling the endpoint the way a client would, and run it. It should fail without your change and pass with it.

C and D add one sentence: "Read and follow .agents/skills/verify-api/SKILL.md, which explains how to do this in this repository." The pointer is needed: left to discover it, the agent opened this skill in 3 of 60 runs. So "the skill" here means the skill and a pointer to it.

No arm has `AGENTS.md` or the other two skills (`safe-change`, `build-test`). The only guidance that differs between B, C and D is the verification skill.

### The revised skill

The revision only reorders and rewords the original. It adds no knowledge of the tasks.

- **First:** write a focused test calling the changed endpoint, which should fail without the change and pass with it. The command to run it uses `<YourTestClass>`.
- **Then:** `ActuatorTest` as the pattern to copy, with the note that it only checks the application starts, so running it does not verify a change.
- **Unchanged:** why the application cannot be started on its own here.

The full difference is in `diff arms/skill-original arms/skill-revised`.

## Tasks

The 20 tasks of verify-vs-skills, repo-skills and explicit-skills, unchanged. That keeps the results comparable with the last three experiments.

On pass rate, half of them do not discriminate: in explicit-skills, every arm passed 8 of them in every run and failed 2 every time. That is one reason pass rate is secondary here.

## Size and cost

20 tasks × 5 arms × 3 runs = **300 runs**. At explicit-skills' costs, this is about $8 to $12, plus the extra grading time below.

Arm E runs in its own trial file, because the rig cannot set effort per arm (as in verify-vs-skills).

## Measures

**Primary: a relevant test.** A run has one if both of these hold:

- the agent added or changed at least one test, outside the hidden tests, and all of them pass with its change;
- at least one of them fails on the original code.

The grader checks this automatically:

1. It runs the agent's own test classes with its change.
2. It restores the original main code, keeps the agent's tests, and runs them again.

A test that does not compile against the original code counts as failing there, and these runs are reported separately. This replaces explicit-skills' proxy, which looked for an added line with `TestRestTemplate` and similar names.

**Secondary:**

- **Verified pass:** the build ran, every hidden test ran and passed, and no existing test failed, as before.
- **Wrote any test**, **ran its own test**, **ran only `ActuatorTest`**, **read the skill**: from the commands the agent ran.
- **Cost** per verified pass and per relevant test, tokens and time.
- **False success claims.**

## Hypotheses and analysis (to be fixed before the runs)

The unit is the task. For each task and arm, the result is the number of runs, out of 3, with a relevant test.

| # | Hypothesis | Test |
| --- | --- | --- |
| H1 | `skill` gives more relevant tests than `instruction`: the skill adds something beyond the instruction | One-sided exact sign-flip permutation test over the 20 tasks |
| H2 | `skill-revised` gives more relevant tests than `skill`: the skill's design matters | As H1 |

- H1 and H2 are Holm-adjusted together at α = 0.05.
- **Secondary**, reported but not tested as hypotheses:
  - relevant tests in `instruction` against `none`;
  - pass rate of every arm against `none`, two-sided, unadjusted, with bootstrap intervals over tasks.
  - **Pass rate is underpowered here.** In explicit-skills, the spread of per-task differences means detecting a 10-point gain needs about 70 tasks, and a 15-point gain about 30 (80% power, one-sided α = 0.05, 3 runs per task). This experiment can show changes in behaviour; it cannot settle small changes in pass rate.
  - `medium` against the best guided arm, on pass rate and cost per verified pass. This compares thinking longer with being told, in the same hours.
- **Exploratory:** the pass rate of runs with and without a relevant test, in each arm. This is not causal.

## Before the runs

1. **Build the relevance check and validate it on explicit-skills' runs.**
   - Apply it to the 25 runs in which a test was detected (15 told in the prompt, 10 told in `AGENTS.md`).
   - Report how many tests fail on the original code. This also checks the proxy used in explicit-skills.
   - The result goes in the amendment log, as an exploratory check on that experiment.
2. **Write `scripts/analyse.py`** and check it on explicit-skills' runs.
3. **Commit the design as final**, then run.

## Known limits

- One repository, one agent, one model, and one verification skill, revised by me. The revision is a reordering, not new knowledge, but I know the tasks.
- B, C and D are all told to write a test. This experiment asks what helps the agent carry that out, not whether it should be told.
- Arm E runs in a second trial file, so it can cover different hours.
- The relevance check shows that a test distinguishes the change from the original, not that it tests the behaviour the task asked for.

## After this: an external check

The next experiment would test a check that does not depend on the agent following instructions. When the agent says it is done, the rig checks, without the hidden tests, that the change includes a relevant test, as defined above. If not, the agent is sent back once with that result. This moves verification from what the agent is asked to do to what is checked when it finishes.

## Amendment log

- 2026-10-22: draft written at the user's request, from a review of explicit-skills. It uses the review's four arms, plus medium effort and the relevance measure.
