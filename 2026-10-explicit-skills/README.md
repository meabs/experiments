# Explicitly called skills (Codex)

Written 2026-10-22, before any run. Later changes go in the amendment log at the bottom.

## Why this follows repo-skills

[2026-10-repo-skills](../2026-10-repo-skills/) gave Codex repository guidance written by an agent: an `AGENTS.md` and three skills. It did not measurably raise the pass rate: 40 of 60 runs passed, against 38 of 60 without guidance (p = 0.40).

The agent did not use the guidance it most needed:

- Every run read `safe-change` and `build-test`.
- Only 8 of 60 runs opened `verify-api`, the skill that explains how to check a change through the API in this repository.
- Only 2 runs wrote a test of their own change.

So repo-skills measured guidance that the agent may choose to read. This experiment asks whether the same guidance helps when the prompt tells the agent to use it.

## Question

With the same repository guidance in place, does telling the agent to use its skills raise the share of changes that pass, compared with no guidance, and compared with the guidance left for the agent to discover?

## Agent and repository

- Codex `gpt-5.6-luna`, reasoning effort low, clean home, the same isolation as before.
- shopizer at `6a4a0a6` (Java, Maven, JDK 21), offline.

## Arms

| Arm | Name | What the agent gets |
| --- | --- | --- |
| A | `none` | The task prompt only |
| B | `discover` | The task prompt, plus the guidance in the clone: `AGENTS.md` and `.agents/skills/`. This repeats repo-skills' arm B |
| C | `explicit` | The same guidance, and the prompt starts with the instruction below |

The guidance in `arms/guidance/` is byte-identical to repo-skills' `arms/repo-skills/` (SHA-256):

- `AGENTS.md` `d814970b…`
- `build-test` `be65f005…`
- `safe-change` `e949cc94…`
- `verify-api` `0c5c0210…`

The instruction for arm C, fixed now and committed as `arms/explicit-prefix.md`, is placed before the task prompt:

> Use this repository's skills in .agents/skills for this task:
> 1. Before you change any code, read and follow .agents/skills/safe-change/SKILL.md.
> 2. To build and run tests, follow .agents/skills/build-test/SKILL.md.
> 3. Before you say you are done, read and follow .agents/skills/verify-api/SKILL.md, and check your change through the API as it says.
>
> The task:

The instruction only says which skill to use and when. All of the how is in the skills.

All three arms run in one trial file, so they cover the same hours. The rig orders runs by repeat, then task, then arm.

## Tasks

The 20 tasks of verify-vs-skills and repo-skills, unchanged: prompts, hidden tests, reference patches and plants.

- 18 runtime traps.
- 2 neighbour breaks (`REVEDIT`, `BOXVIS`).

The tasks were selected in verify-vs-skills on arm A's calibration runs, which favours arm A slightly. That makes H1 conservative.

## Size and cost

20 tasks × 3 arms × 3 runs = **180 runs**. At repo-skills' costs, this is about $1 each for arms A and B, and $1 to $2 for arm C, which is likely to test more.

## Measures

**Primary:** verified pass. The build ran, every hidden test ran and passed, and no existing test failed.

**Secondary:**

- **Compliance:** which skills each run read, from the commands it ran.
- **Process:** ran Maven tests; wrote tests; wrote an API-level test; tried to start the application.
- **Cost:** cost per verified pass (pooled), tokens and time.
- **Neighbour breaks:** on the 2 neighbour-break tasks.
- **False success claims.**

## Hypotheses and analysis (fixed now)

The unit is the task. For each task and arm, the result is passes out of 3.

| # | Hypothesis | Test |
| --- | --- | --- |
| H1 | `explicit` raises the pass rate over `none` | One-sided exact sign-flip permutation test over the 20 tasks, on the per-task difference in passes |
| H2 | `explicit` raises the pass rate over `discover` | As H1 |

- H1 and H2 are Holm-adjusted together at α = 0.05.
- Effects are the mean per-task difference in pass rate, with a bootstrap interval over tasks (10,000 resamples, seed 1).
- **Secondary**, two-sided and unadjusted: `discover` against `none`, which repeats repo-skills' H1. Also cost per verified pass against `none`, for B and C, and the measures above.
- **Exploratory**, and labelled so:
  - in arms B and C, the pass rate of runs that did and did not read `verify-api`, and that did and did not write an API-level test;
  - results by kind of task.
- `scripts/analyse.py` is committed with this README. It was checked on repo-skills' runs, with its arm B standing in for both B and C.

**What it can detect.** As in repo-skills: a gain of about 15 to 20 points.

## Known limits

- One repository, one agent, one model, and one set of guidance, written by an agent in repo-skills.
- Arm C's instruction adds text that arm B does not have. A gain for C could come from the extra emphasis on verifying, not only from reading the skills. The compliance measures show whether C actually read `verify-api`.
- Only 2 neighbour-break tasks.

## Reproducing

```
python3 -I scripts/make_trial.py && scripts/localize.sh
trialrig run trial.local.toml --out <dir> --agent codex
scripts/export.sh <dir> stage1
python3 -I scripts/analyse.py results/stage1/runs > results/analysis.md
```

## Amendment log

- 2026-10-22: design written at the user's request, following repo-skills: "an experiment where we explicitly call the skills, not just allow discovery". Codex only.
- 2026-10-22 (main trial running, 29 of 180 runs done, no result looked at or analysed): **arm D added at the user's request**, "an entry in AGENTS.md telling it to use the verification skills".
  - **What D gets.** The same guidance, with one entry added to the end of `AGENTS.md`, in `arms/guidance-agentsmd/`. Its words are those of arm C's third step:

    > ## Before you finish
    >
    > Before you say you are done, read and follow `.agents/skills/verify-api/SKILL.md`, and check your change through the API as it says.

    The skills are unchanged.
  - **What it isolates.** C tells the agent in the prompt, which a user writes for each task. D puts the instruction in the repository, where a team would put it once. D names only the verification skill: in repo-skills, the agent already read the other two in every run.
  - **How it runs.** The rig cannot add an arm to a running trial, so D runs as a second trial file, `trial-agentsmd.toml`, started while the main trial is running. Otherwise it is identical: same tasks, 3 runs each, low effort. Its runs cover later hours than A to C's. This is noted as a limit.
  - **New hypotheses**, tested as H1 and H2 are:
    - H3: `agentsmd` beats `none`;
    - H4: `agentsmd` beats `discover`.

    H3 and H4 are Holm-adjusted as their own pair, so H1 and H2 and their adjustment are unchanged.
  - **Secondary**, two-sided and unadjusted: `explicit` against `agentsmd`.
  - **Analysis.** `analyse.py` takes D's runs as an optional second folder. It was checked on repo-skills' runs before D started.
