# The swarm tax: does a team of agents beat one agent with the same budget? (Codex)

**Draft design, written 2026-10-26 before any run. Not yet final: it becomes final when committed with the user's go-ahead, and later changes go in the amendment log at the bottom.**

## Why

Multi-agent coding is sold as the next step after a single agent: a planner splits the work, coders write it, a reviewer checks it. The demos usually show the team doing better. But they rarely hold the budget fixed. The team gets several agents' worth of tokens, retries and time, against one agent's.

So a team's gain could come from two places:

- **the structure:** planning, splitting the work, an independent review;
- **the spend:** more tokens and more attempts, which a single agent could also be given.

The [EGM pilot](../2026-10-egm-pilot/REPORT.md) is a warning here. EGM's fresh-context reviewers did no better than a plain plan-first process, at about five times the cost, and the decisive fix came from the human approver, never from a reviewer. That was 3 runs per arm on one feature. This experiment asks the general question with enough runs to test it, and with the spend matched.

## Question

On the same tasks and model, does a Codex agent team (planner, coder and reviewer subagents) produce more correct changes than one Codex agent? And does any gain survive when the single agent is given the same spend, as several independent attempts?

## Agent and repository

- Codex `gpt-5.6-luna` (CLI 0.157), low reasoning effort, clean home, the same rig and isolation as [test-skill](../2026-10-test-skill/).
- shopizer at `6a4a0a6` (Java, Maven, JDK 21), offline.
- **Teams use Codex's own subagents** (`--enable multi_agent_v2`), as in the EGM pilot: without the flag, Codex 0.157 has no subagent tool. No outside framework, so the only difference between arms is how the work is organised.

## Arms

| Arm | Name | What the agent gets |
| --- | --- | --- |
| S | `solo` | The task prompt only, as arm A of test-skill |
| T | `team` | The task prompt, after a team instruction ([`arms/team.md`](arms/team.md)): the main agent plans and does not edit code; it spawns one coder subagent to make the change and one reviewer subagent, started with no conversation history, to check it; at most one round of fixes after the review |
| F | `team-full` | As T, scaled up as in vendor demos ([`arms/team-full.md`](arms/team-full.md)): the planner may split the work across up to two coders; at most three rounds of review and fixes |
| K | `solo-best-of-k` | Not a separate run. k independent `solo` runs, of which one is kept by a rule that does not use the hidden tests (below). This is the single agent given the team's spend |

- **Team prompts are written to give the team a fair chance**, following the published patterns (a planner that writes a short plan first, a reviewer that reads the diff, runs the tests and reports concrete faults). Every reviewer is spawned with `fork_turns "none"`, the EGM pilot's correction, so it really starts fresh.
- **Every subagent sees the same repository and tools** as the solo agent. None sees the hidden tests.
- T and F run in their own trial file, with the subagent flag; S runs alongside them on the same day.

### Matching the spend (arm K)

Codex cannot stop a session at a token budget, so the budget is matched after the runs, not enforced during them:

- **k** = the ratio of T's mean tokens per run to S's mean tokens per run, over all 20 tasks, rounded to the nearest whole number, at least 2 and at most 5. Tokens are every session's tokens, subagents included, read from the session files (subagent tokens are not in the main event stream; EGM pilot). This rule is fixed now; k is computed once, after the runs.
- **Which attempt is kept.** Attempts are taken in order, and the first one that passes the **visible check** is kept: the build compiles and the agent's own tests, if it wrote any, pass with its change. If none passes, the last is kept. This is what a person or a script could do without the hidden tests.
- **Estimate.** Each task has 5 solo runs. K's pass rate for a task is the average, over every ordering of its 5 runs, of whether the kept run among the first k passes. This uses all runs and needs no random draw.
- F gets the same treatment, with its own k (cap 5), as a secondary comparison.

## Tasks

- **The 20 small fixes** of verify-vs-skills, repo-skills, explicit-skills and test-skill, unchanged, so results sit beside the last four experiments.
  - Known weakness: in explicit-skills, 8 tasks passed in every run and 2 failed in every run. A team cannot improve those. This is reported, and the analysis is per task.
- **One feature, DISCOUNT**, from the EGM pilot, unchanged: merchant discount codes, 16 hidden API tests, reference implementation touching 7 files across 4 modules. Small fixes leave little for planning or splitting the work to do, so a feature gives the team its best case. Scored as hidden tests passed out of 16. Plain Codex at low effort scored 4 and 2 there.

## Size and cost

| | Runs |
| --- | --- |
| 20 fixes: S 5 per task, T 3, F 3 | 100 + 60 + 60 = 220 |
| DISCOUNT: S 5, T 3, F 3 | 11 |
| **Total** | **231** |

- **API cost: roughly $20 to $40.** Solo runs cost about $0.02 each in test-skill (0.44M tokens). Team runs are guessed at 4 to 10 times that; the smoke test (below) will replace the guess before the runs start.
- **Time:** grading (hidden tests plus the full existing suite, plus the relevance check) takes 5 to 10 minutes a run and dominates. At 3 runs in parallel, about 8 to 12 hours.

## Local model: not in this experiment

The protocol compares a local open-weight model with the hosted one. That is not possible here:

- In [test-skill-local](../2026-10-test-skill-local/), every local run on these tasks hit its time limit. One smoke run with no time limit passed, but took 1 h 55 min and 7.5M tokens, against 53 s for the hosted model.
- A team multiplies that. 231 runs would take weeks.

So this experiment is hosted only, and makes no local-versus-hosted claim. If wanted, a later local pilot could run T against S on DISCOUNT alone.

## Measures

**Primary: verified pass** (per task, the share of runs that pass), as in every earlier experiment: the build ran, every hidden test ran and passed, and no existing test failed. On DISCOUNT, hidden tests passed out of 16.

**Secondary:**

- **Tokens** (input, cached, output, reasoning), **cost** at list prices, **wall time**, all sessions included.
- **Cost per verified pass**, per arm.
- **The rubber stamp rate:** in T and F, the share of runs whose final review approved the change but the hidden tests fail. Read from the reviewer subagent's own session, not from the planner's summary.
- **What the review caught:** of review rounds that asked for a fix, how many runs went from failing to passing the visible check after it.
- **False success claims:** the final message says the change is done and correct, but it fails.
- **Did the team really happen:** for each T and F run, from the session files: how many subagents were spawned, with which `fork_turns`, whether the planner itself edited code. A team run that spawned no subagents is still counted in its arm (it is what the arm produced), and the number is reported.

## Hypotheses and analysis (fixed before the runs)

The unit is the task. For each task and arm, the result is the pass rate (S out of 5, T and F out of 3, K as estimated above). Differences are per task; tests are exact sign-flip permutation tests over the 20 tasks, with bootstrap 95% intervals (10,000 resamples, seed 1), reusing [`2026-10-skills-impact/scripts/stats.py`](../2026-10-skills-impact/scripts/stats.py).

| # | Hypothesis | Test |
| --- | --- | --- |
| H1 | `team` passes more than `solo`: the claim as demonstrated, spend not matched | One-sided |
| H2 | `team` and `solo-best-of-k` differ: whether the team's structure is worth more than the same spend on independent attempts | Two-sided |
| H3 | `team-full` passes more than `team`: whether a bigger team helps | One-sided |

- H1 to H3 are Holm-adjusted together at α = 0.05.
- **How to read them together:**
  - H1 true and H2 showing no difference: the team's gain is the spend, not the structure.
  - H2 in the team's favour: the structure adds something beyond more attempts.
  - H1 false: on these tasks, a team does no better than one agent even with several times the budget.
- **Secondary**, reported, not tested as hypotheses: `team-full` against its own best-of-k; cost per verified pass for every arm; the rubber stamp rate; DISCOUNT results, per run (11 runs is too few to test).
- **Power.** From explicit-skills' spread, 20 tasks can detect a gain of about 15 points in pass rate (80% power, one-sided α = 0.05). A smaller gain will show as "no measurable difference", which means just that.

## Before the runs

1. **Check subagents work under the rig.** Run T and F once each on SUPERDEL and TAXRATE (not counted). Confirm from the session files that the subagents spawn with `fork_turns "none"`, that the planner did not edit code, that the subagents stayed inside the clone, and that every session's tokens are found. Confirm no subagent ran `mvn install` and the shared Maven repository is unchanged (checksum of `com/shopizer`).
2. **Measure team cost** in those smoke runs and replace the cost estimate above.
3. **Write `scripts/analyse.py`**, including the best-of-k estimate, and check it on test-skill's arm A runs (with a fake team arm) so every section runs before any measured result exists.
4. **Commit the design as final**, with the smoke-test results, and push it before the measured runs, with the user's go-ahead.

## Known limits

- One repository, one model, one effort level, and team prompts written by me. A different team design might do better; the prompts are published so that can be checked.
- **The budget is matched after the fact, by tokens.** Time is not matched: a team's subagents can run in parallel, so a team may finish sooner than k attempts in a row. Wall time is reported for every arm.
- **Best-of-k's selection is weak by design.** It uses only the build and the agent's own tests. A stronger selector (for example, a model judging the diffs) could favour K more; the diff-judge experiment found such a judge barely better than chance on these tasks, so it is not used.
- The 20 fixes are small. Ten of them gave the same result in every run in earlier experiments. DISCOUNT is the only task where the team's structure has much room, and it has 11 runs.
- Codex's subagent feature is behind a flag in 0.157 and may change.
- No local-model comparison (above).

## Amendment log

- 2026-10-26: draft written at the user's request ("Based on the theme of my site I want one new experiment idea that challenges and tests something in industry hype" … "Yes please"). Not yet final; no run made.
