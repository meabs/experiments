# Do skill packs help across many different tasks? (Codex)

Written 2026-10-21, before any measured run. Later changes go in the amendment log at the bottom. Draft: the task list is being built and is not frozen yet.

## Why this follows skills-impact

[2026-10-skills-impact](../2026-10-skills-impact/) ran 6 repeats of each of 3 tasks. Its review ([REPORT.md](../2026-10-skills-impact/REPORT.md)) found that repeats of one task tell you how variable the agent is on that task, not whether a pack helps on tasks in general. Its pass-rate result rested on a single task (Codex on CROSS), and two of its three tasks were at the ceiling for the control.

This experiment keeps the question and the arms, drops Cursor (no credits), and spends the runs on many different tasks instead of repeats.

## Question

On a varied set of real change tasks, do Superpowers or Matt Pocock's skills raise the share of changes that pass independent acceptance tests, and at what cost in tokens?

## Agent and repository

- Codex `gpt-5.6-luna`, reasoning effort high, with the same clean home, isolation and rig version as skills-impact.
- shopizer at `6a4a0a6`. The verifier, isolation and hardened `summarize.py` are reused from skills-impact.

## Arms

`none`, `placebo`, `superpowers` and `pocock`, built exactly as in skills-impact (same pinned commits, same `AGENTS.md` bootstrap for Superpowers). pstack is left out because it ships only for Cursor and Claude Code.

## Tasks

- **Candidates:** about 20 new tasks, none of them reused from skills-impact. They cover bug fixes (a single cause, two causes, and a symptom far from its cause), small features, cross-module fields, and validation and error handling. They span catalog, cart, customer, content, tax and store code.
- **What each task has:**
  - a prompt written as a merchant or developer would write it, which never mentions skills, tests or tools;
  - a hidden API-level acceptance test that fails on the starting code and passes with a reference patch;
  - a full suite that passes with the reference applied.
- **Selection (fixed now):** `none` runs each candidate twice in calibration, and those runs are discarded. The 16 candidates with the lowest calibration pass rate are kept, with ties broken by candidate number. Selecting on the control's calibration runs avoids filling the experiment with tasks every arm solves, and the measured runs are fresh, so it does not favour any arm.

## Size and cost

16 tasks × 4 arms × 2 runs = **128 runs**, plus 40 calibration runs. At skills-impact's measured Codex cost ($0.08 a run without skills, $0.18 with Superpowers), that is about **$15 to $20**.

Two runs per task, not one, so that within-task noise can be estimated. The unit of analysis is the task.

## Measures

- **Primary:** verified pass (the hardened `summarize.py`: the build ran, every hidden test ran and passed, nothing skipped, no other test failed).
- **Secondary:**
  - tokens (fresh input, cached input and output reported separately);
  - wall time;
  - Maven test runs;
  - production lines and test lines changed;
  - skill uptake;
  - test-file-first and confirmed TDD (`process.py` from skills-impact);
  - overclaims.

## Hypotheses and analysis (fixed now)

| # | Hypothesis | Test |
| --- | --- | --- |
| T1 | Superpowers raises the pass rate | Per task, the difference in passes between `superpowers` and `none` (each 0 to 2). A one-sided exact sign-flip permutation test over tasks, with α = 0.05. The effect is reported as the mean per-task difference with a bootstrap interval over tasks |
| T2 | Pocock raises the pass rate | As T1 |
| T3 | Placebo has no effect (a check on T1 and T2) | As T1, two-sided, reported only |

- T1 and T2 are Holm-adjusted together.
- A pack's gain counts as a pack effect only if it is larger than the placebo's.
- Tokens are reported as the mean per-task ratio to `none`.
- Exploratory, labelled as such: results by task type, and Pocock conditional on a skill being read.

## Known limits

- One repository and one agent. Claude writes the tasks, plants, reference patches and hidden tests, and they are committed for review.
- Planted bugs are not real bugs, and a model trained on shopizer may know the original code.

## Amendment log

- 2026-10-21: draft written at the user's request ("increase the number of different tests, not the number of runs"; Codex only).
