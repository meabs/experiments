# Repository skills (Codex)

Written 2026-10-22, before the skills were generated and before any run. Later changes go in the amendment log at the bottom.

## Why this follows verify-vs-skills

[2026-10-verify-vs-skills](../2026-10-verify-vs-skills/) found that a one-paragraph instruction to check the change against the running application did not raise the pass rate (39 of 60 runs, against 36 of 60 with nothing). The likely reason: the instruction said *what* to do, not *how* to do it in this repository.

- The agent tried to start the application in 47 of 60 runs, but shopizer does not start outside its tests without extra set-up. The application answered in only 3 runs.
- The instruction offered another route, a test that starts the application. Only 5 runs took it.

Generic skills ([Superpowers](../2026-10-skills-tasks/)) have not helped in two experiments either. The open question is whether guidance written *for this repository* does: how to build it, how to test a change against its API, and where its traps are.

## Question

Does repository-specific guidance (an `AGENTS.md` and a set of skills, written by an agent from the repository) raise the share of changes that pass independent acceptance tests, compared with no guidance? At what cost?

## Agent and repository

- Codex `gpt-5.6-luna`, reasoning effort low, clean home, the same isolation as before. Low effort leaves room to improve: at medium effort, Codex passed 49 of 60 runs on these tasks.
- shopizer at `6a4a0a6` (Java, Maven, JDK 21), offline.

## Arms

| Arm | Name | What the agent gets |
| --- | --- | --- |
| A | `none` | The task prompt only |
| B | `repo-skills` | The task prompt, plus the generated `AGENTS.md` at the repository root and the generated skills under `.agents/skills/` |

Both arms run in one trial file, so they cover the same hours. Arm A is run again rather than reusing verify-vs-skills' arm A, for the same reason.

## How the guidance is generated

The guidance is written by an agent, not by me. I wrote the tasks and know their causes, so anything I wrote would lean towards them.

- **The agent.** Codex `gpt-5.6-luna` at high reasoning effort, one run, through the rig (`generate/generate.toml`).
- **The brief.** [`generate/brief.md`](generate/brief.md), committed with this README. It asks for an `AGENTS.md` and skills covering, at least:
  - building and testing;
  - verifying a change against the running application, or through a test that starts it;
  - making changes safely: request flow, error handling, and checking the other users of shared code.

  It asks the agent to run every command it recommends, and to recommend only commands it saw work.
- **What it cannot see.** It works in a fresh clone of shopizer at `6a4a0a6`, with its own home folder. All of `~/code` is hidden from it by the rig's sandbox: these experiments, earlier runs, and my notes. So it never sees the task prompts, the hidden tests or the fixes.
- **What is kept.** Only `AGENTS.md` and `.agents/` are copied to `arms/repo-skills/` (`scripts/capture.sh`). Anything else the agent changed is discarded, and listed in the generation record.
- **Used as generated.** The guidance is committed before any measured run and not edited. If the generation run fails (no `AGENTS.md`, or no skill), it is run once more and the amendment log says so.
- **Whether it names a task's cause.** After generation and before the runs, I will note in the amendment log any passage that describes the specific cause of one of the 20 tasks. This is recorded, not removed. Knowing the repository's real traps is what repository guidance is for, and the agent found them without seeing the tasks.

## Tasks

The 20 tasks of verify-vs-skills, unchanged: prompts, hidden tests, reference patches and plants. They were validated there (`tasks/*/validation.json`).

- **Runtime traps (18).** The obvious change compiles but is wrong when the application runs.
- **Neighbour breaks (2).** `REVEDIT` and `BOXVIS`: the obvious change breaks another feature that shares the code. Their `keeps…` hidden tests check that feature.

There is no new calibration or selection. The tasks were selected in verify-vs-skills using arm A at low effort, the same as arm A here. That favours arm A slightly, through regression to the mean, which makes H1 conservative.

## Size and cost

20 tasks × 2 arms × 3 runs = **120 runs**. At verify-vs-skills' costs, this is about $1 for arm A and $1 to $3 for arm B, plus about $1 for the generation run.

## Measures

**Primary:** verified pass. The build ran, every hidden test ran and passed, and no existing test failed.

**Secondary:**

- cost per verified pass (pooled), and tokens and time;
- neighbour breaks: runs where a `keeps…` test fails, on the 2 neighbour-break tasks;
- false success claims: failed runs whose end-of-run claim says the change works;
- process:
  - read a skill;
  - ran Maven tests;
  - wrote tests;
  - wrote an API-level test;
  - tried to start the application;
  - called it.

## Hypotheses and analysis (fixed now)

The unit is the task. For each task and arm, the result is passes out of 3.

| # | Hypothesis | Test |
| --- | --- | --- |
| H1 | `repo-skills` raises the pass rate over `none` | One-sided exact sign-flip permutation test over the 20 tasks, on the per-task difference in passes, α = 0.05 |

- The effect is the mean per-task difference in pass rate, with a bootstrap interval over tasks (10,000 resamples, seed 1).
- Secondary, reported but not tested:
  - cost per verified pass (`repo-skills` over `none`, tasks resampled for the interval);
  - neighbour breaks;
  - false success claims;
  - the process measures.
- Exploratory, and labelled so:
  - in arm B, the pass rate of runs that did and did not write an API-level test or run Maven tests;
  - results by kind of task.
- `scripts/analyse.py` is written and committed with this README. It was checked on verify-vs-skills' runs, with Superpowers standing in for arm B.

**What it can detect.** With 20 tasks, 3 runs each and the spread seen in verify-vs-skills, a gain of about 15 to 20 points is detectable; smaller gains would likely be missed. Medium effort gained 21.7 points there.

## Known limits

- One repository, one agent, one model, one generated set of guidance. A different generation run could write better or worse guidance. This tests one draw, not "repository skills" in general.
- The guidance is both an `AGENTS.md` and skills, so the experiment does not separate the two formats.
- Arm B adds text, and so cost, to every run. Cost per verified pass is the comparison on cost.
- Only 2 neighbour-break tasks, so little can be said about neighbour breaks.

## Reproducing

```
python3 -I scripts/make_trial.py && scripts/localize.sh
trialrig run generate/generate.local.toml --out <gen> --agent codex   # writes the guidance
# copy <gen>/runs/GENERATE/none/codex/1/generated/ to arms/repo-skills/
trialrig run trial.local.toml --out <dir> --agent codex
scripts/export.sh <dir> stage1
python3 -I scripts/analyse.py results/stage1/runs > results/analysis.md
```

## Amendment log

- 2026-10-22: design written at the user's request, following verify-vs-skills. Codex only. Two arms, as the user asked: no guidance, and agent-generated `AGENTS.md` plus skills.
