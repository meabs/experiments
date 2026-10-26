# The swarm tax: does a team of agents beat one agent with the same budget? (Codex)

**Final design, committed and pushed 2026-10-26 before any measured run.** Later changes go in the amendment log at the bottom.

## Why

Multi-agent coding is sold as the next step after a single agent: a planner splits the work, coders write it, a reviewer checks it. The demos usually show the team doing better. But they rarely hold the budget fixed. The team gets several agents' worth of tokens, retries and time, against one agent's.

So a team's gain could come from two places:

- **the structure:** planning, splitting the work, an independent review;
- **the spend:** more tokens and more attempts, which a single agent could also be given.

The [EGM pilot](../2026-10-egm-pilot/REPORT.md) is a warning here. EGM's fresh-context reviewers did no better than a plain plan-first process, at about five times the cost, and the decisive fix came from the human approver, never from a reviewer. That was 3 runs per arm on one feature. This experiment asks the general question on six features, with the spend matched.

## Question

On the same feature tasks and model, does a Codex agent team (planner, coder and reviewer subagents) get more of a feature right than one Codex agent? And does any gain survive when the single agent is given the same spend, as several independent attempts?

## Agent and repository

- Codex `gpt-5.6-luna` (CLI 0.157), **medium reasoning effort in every arm and every subagent**. The EGM pilot found low effort too little for a feature (the build stops short), and at medium a single agent still leaves most of DISCOUNT undone (smoke test, below).
- shopizer at `6a4a0a6` (Java, Maven, JDK 21), offline, on this machine (Linux): Codex runs inside bubblewrap (`local-setup/codex-bwrap.sh`) with a fresh home per run holding only the login, as in test-skill-local's hosted calibration. The experiments folder, the hidden tests and every other run are invisible to the agent.
- **Teams use Codex's own subagents** (`--enable multi_agent_v2`), as in the EGM pilot. No outside framework, so the only difference between arms is how the work is organised. Subagents inherit the main session's model and effort (checked in the session files).

## Arms

| Arm | Name | What the agent gets |
| --- | --- | --- |
| S | `solo` | The task prompt only |
| T | `team` | The task prompt, after a team instruction ([`arms/team.md`](arms/team.md)): the main agent plans and must not edit files; it spawns one coder subagent to make the change and one reviewer subagent, started with no conversation history, to check it; at most one round of fixes after the review |
| F | `team-full` | As T, scaled up as in vendor demos ([`arms/team-full.md`](arms/team-full.md)): the planner may split the work across up to two coders; at most three rounds of review and fixes |
| K | `solo-best-of-k` | Not a separate run. k independent `solo` runs, of which one is kept by a rule that does not use the hidden tests (below). This is the single agent given the team's spend |

- **Team prompts give the team a fair chance**, following the published patterns: a planner that writes a short plan first, a reviewer that reads the diff, runs the tests and reports concrete faults, ending with `VERDICT: APPROVE` or `VERDICT: CHANGES`. Every subagent is spawned with `fork_turns "none"`, the EGM pilot's correction, so the reviewer really starts fresh. The prompts name the collaboration tools and say to call them directly, because Codex's instructions say they cannot be called from inside its `exec` tool.
- **Every subagent sees the same repository and tools** as the solo agent. None sees the hidden tests.
- **Each arm has its own trial file**, with the arm's instruction written into every task prompt by [`scripts/make_trial.py`](scripts/make_trial.py) (below, "The rig dropped arm prompts"). The three trial files run side by side.

### Matching the spend (arm K)

Codex cannot stop a session at a token budget, so the budget is matched after the runs, not enforced during them:

- **k** = the ratio of T's mean cost per run to S's mean cost per run, over all tasks, rounded to the nearest whole number, at least 2 and at most 6. Cost covers every session, subagents included, read from the session files ([`scripts/audit_run.py`](scripts/audit_run.py)); subagent tokens are not in the rig's event stream. F gets its own k the same way. This rule is fixed now; each k is computed once, after the runs.
- **Which attempt is kept.** Attempts are taken in order, and the first that passes the **visible check** is kept: the change compiles with no hidden tests present (`visible.json`), and the agent's own tests, if it wrote any, pass with its change (`relevance.json`). If none passes, the last is kept. This is what a person or a script could do without the hidden tests.
- **Estimate.** Each task has 6 solo runs. K's score for a task is the average, over every ordering of those runs, of the score of the run kept from the first k. This uses all runs and needs no random draw.

## Tasks

Six features, each stated as a need with the interface the tests use fixed (paths, JSON fields, status codes, rules), and nothing about how to build it. Each has hidden API tests and a reference implementation that I wrote, validated before any run ([`scripts`](scripts/) and below).

| Task | What it asks for | Hidden tests | Reference: files, added lines | Hidden tests failing on the original code |
| --- | --- | --- | --- | --- |
| [DISCOUNT](tasks/DISCOUNT/prompt.md) | Merchant discount codes replacing a hard-coded promo rule (from the EGM pilot, unchanged) | 16 | 7, about 440 | 15 |
| [TIERPRICE](tasks/TIERPRICE/prompt.md) | Quantity price tiers per product, applied to cart lines | 14 | 5, 193 | 13 |
| [WISHLIST](tasks/WISHLIST/prompt.md) | A logged-in customer's wishlist, move to cart, the store's most wished products | 15 | 4, 284 | 13 |
| [BACKINSTOCK](tasks/BACKINSTOCK/prompt.md) | Back-in-stock alerts sent to an outbox when stock rises from zero; includes making the existing inventory update work for API-created products | 13 | 10, 352 | 12 |
| [PRODUCTQA](tasks/PRODUCTQA/prompt.md) | Product questions with moderation (answer to publish, reject) | 14 | 4, 276 | 11 |
| [CARTLIMIT](tasks/CARTLIMIT/prompt.md) | Per-product purchase limits and store cart caps, enforced on every cart change, with warnings on the cart | 14 | 13, 379 | 12 |

- **Validation** ([`scripts/validate.sh`](scripts/validate.sh)): with the reference applied, every hidden test passes and the whole existing suite still passes; on the original code, the counts above fail. The tests that pass on the original check things it already does (an admin token is required, an unknown id gives 404).
- **BACKINSTOCK states a fix.** The existing inventory update fails for products created through the API, and when no prices are given. The prompt says so and requires it to work, because the tests restock through it. Nothing else the tests need is hidden in the prompt.
- **Why features, not the 20 small fixes of the earlier experiments.** In the first smoke tests, a single agent finished those fixes in 25 to 50 seconds. A team has nothing to plan, split or review there, so the comparison would be decided by the tasks, not the team.

## Size and cost

| | Runs |
| --- | --- |
| S: 6 tasks × 6 runs | 36 |
| T: 6 × 6 | 36 |
| F: 6 × 6 | 36 |
| **Total** | **108** |

- **API cost: about $15 to $25.** From the DISCOUNT smoke test at medium effort: solo $0.075, team $0.073, team-full $0.31 per run (every session counted).
- **Time:** a team-full run took 9 minutes, and grading (visible check, relevance check, hidden tests and the whole existing suite) takes 5 to 10 minutes a run. With the three trial files side by side, each 3 runs at a time, about 6 to 9 hours.
- **Time limits:** 45 minutes for solo, 60 for the team arms. A run that times out is graded as it stands.

## Measures

**Primary: the share of hidden tests passed** (per run, passed ÷ the task's hidden tests). A feature is rarely all right or all wrong: solo passed 2 of DISCOUNT's 16 tests in the smoke test. A run whose change does not compile scores 0.

**Secondary:**

- **Verified pass:** every hidden test passed and no existing test failed, as in earlier experiments.
- **Cost** at list prices, **tokens** (input, cached, output, reasoning), **wall time**, all sessions included; **cost per hidden test passed**.
- **The rubber stamp rate:** in T and F, the share of runs whose last review said `VERDICT: APPROVE` while hidden tests fail. Read from the reviewer subagent's own session, not from the planner's summary.
- **What the review caught:** of runs where a review said `CHANGES`, the hidden-test score of the final change, against runs where the first review approved.
- **Did the team really happen:** for each T and F run, from the session files: subagents spawned and their `fork_turns`, whether the planner edited files itself, the number of review rounds. A team run that spawned no subagents is still counted in its arm (it is what the arm produced), and the number is reported.
- **False success claims:** the final message says the work is done and correct, but hidden tests fail.

## Hypotheses and analysis (fixed before the runs)

Scores are per run. Arms are compared by the mean, over the 6 tasks, of each task's mean score, so every task counts equally.

| # | Hypothesis | Test |
| --- | --- | --- |
| H1 | `team` scores higher than `solo`: the claim as demonstrated, spend not matched | One-sided permutation test, arm labels shuffled within each task |
| H2 | `team` and `solo-best-of-k` differ: whether the team's structure is worth more than the same spend on independent attempts | Two-sided, bootstrap within each task (team runs and solo runs resampled, K recomputed from the resampled solo runs) |
| H3 | `team-full` scores higher than `team`: whether a bigger team helps | One-sided permutation test, as H1 |

- Permutation tests use 100,000 random shuffles (seed 1); the bootstrap and all effect intervals use 10,000 resamples within tasks (seed 1). H1 to H3 are Holm-adjusted together at α = 0.05.
- **How to read them together:**
  - H1 true and H2 showing no difference: the team's gain is the spend, not the structure.
  - H2 in the team's favour: the structure adds something beyond more attempts.
  - H1 false: on these features, a team does no better than one agent.
- **Secondary**, reported, not tested as hypotheses: `team-full` against its own best-of-k; verified passes per arm; cost per hidden test passed; the rubber stamp rate; per-task results.
- **Power.** Six tasks is few, and features vary a lot between runs. A difference of under about 15 points in the share of hidden tests passed will likely show as "no measurable difference", which means just that.

## The rig dropped arm prompts

The first two smoke tests (8 team runs on SUPERDEL and TAXRATE, low effort) showed no team at all: the planner did all the work itself. The session files showed why. **The team instruction never reached the agent.** The installed AgentTrialRig (0.7.0) has no per-arm `prompt_prefix`: the key was accepted and silently ignored, so every arm sent the bare task. The Mac runs of test-skill did get their arm text, so the Mac's copy of the rig had the option, unpushed.

- **This experiment** writes each arm's instruction into the task prompts itself, so it does not depend on the rig. Every run's prompt is in its Codex session file and is checked.
- **The rig** is fixed in [AgentTrialRig PR #3](https://github.com/meabs/AgentTrialRig/pull/3) (per-arm `prompt_prefix` and `prompt_suffix`, unknown keys rejected, each run's prompt saved), opened at the user's request and not yet merged.
- **test-skill-local's arm G** (`stop`) ran on this machine with the same rig, so its sentence never reached the agent either: it was arm A twice. That pilot was stopped and never analysed, so no published result changes; its README gets a note.

## Before the runs

1. **Subagents under the rig. Done.** DISCOUNT at medium effort, one run per arm (not counted):

   | Arm | Hidden tests | Time | Subagents (all `fork_turns: none`) | Planner edited files | Tokens | Cost |
   | --- | --- | --- | --- | --- | --- | --- |
   | solo | 2/16 | 2 min | none | (alone) | 2.35M | $0.075 |
   | team | 2/16 | 3 min | coder, reviewer (CHANGES) | no | 1.91M | $0.073 |
   | team-full | 4/16 | 9 min | two coders in parallel, three reviewers (CHANGES each time) | no | 10.25M | $0.31 |

   No run read a path outside its clone or ran `mvn install`, and the shared Maven repository was unchanged (checksum of `com/shopizer` before and after).
2. **Tasks built and validated. Done** (table above).
   - **Grader check:** one solo run per new task through the final grader (not counted): every change compiled, no existing test broke, and the shared Maven repository was unchanged. Hidden tests passed: PRODUCTQA 14/14, TIERPRICE 13/14, WISHLIST 12/15, BACKINSTOCK 6/13, CARTLIMIT 2/14, in 98 to 158 seconds each. One run is not an estimate, but PRODUCTQA and TIERPRICE may leave little room above solo; this is reported with the results, and the tasks were not changed after seeing it.
3. **Analysis script written and checked. Done.** [`scripts/analyse.py`](scripts/analyse.py) ran on the three DISCOUNT smoke runs and every section ran. Its best-of-k closed form matched a brute-force average over every ordering in 300 random cases (largest difference 1.4e-14).
4. **Design committed as final and pushed, then run. Done** (the user: "Go for it").

## Known limits

- One repository, one model, one effort level; team prompts, tasks, tests and references written by me. The prompts and tests are published so they can be checked.
- **The budget is matched after the fact, by cost.** Time is not matched: a team's subagents can work in parallel. Wall time is reported for every arm.
- **Best-of-k's selection is weak by design.** It uses only compiling and the agent's own tests. A stronger selector (for example, a model judging the diffs) could favour K more; the diff-judge experiment found such a judge barely better than chance on these tasks, so it is not used.
- Six tasks. The answer could differ on other kinds of work.
- Codex's subagent feature is behind a flag in 0.157 and may change.
- **No local model.** The protocol compares a local open-weight model with the hosted one. In [test-skill-local](../2026-10-test-skill-local/), every local run on the small fixes hit its time limit, and one untimed run took nearly two hours; teams on features would take weeks. At the user's direction ("Use codex and Luna model"), this experiment is hosted only and makes no local-versus-hosted claim.

## Reproducing

```
python3 -I scripts/make_trial.py
cd ~/code/benchmark/AgentTrialRig
uv run trialrig run ~/code/experiments/2026-10-swarm-tax/trial-solo.local.toml --agent codex --out <dir>/solo
uv run trialrig run ~/code/experiments/2026-10-swarm-tax/trial-team.local.toml --agent codex --out <dir>/team
uv run trialrig run ~/code/experiments/2026-10-swarm-tax/trial-team-full.local.toml --agent codex --out <dir>/team-full
```

## Amendment log

- 2026-10-26: first draft written at the user's request ("Based on the theme of my site I want one new experiment idea that challenges and tests something in industry hype" … "Yes please"): 20 small fixes plus DISCOUNT, low effort.
- 2026-10-26, before any measured run: hosted only, at the user's direction ("Use codex and Luna model , progress").
- 2026-10-26, before any measured run: effort raised to medium and the tasks replaced by six features, at the user's request ("Up the reasoning if needed and endure change is complex enough"). The small fixes were dropped after the smoke tests showed a single agent finishing them in under a minute. Primary measure changed from verified pass to the share of hidden tests passed, and the tests from per-task sign-flips to within-task permutation and bootstrap, because six tasks are too few for a sign-flip test across tasks.
- 2026-10-26, before any measured run: the rig's dropped arm prompts found and worked around; the rig fix opened as PR #3 at the user's request ("Fix the rig and push a pr as well"). The team prompts were made explicit about the collaboration tools before the cause was found; they are kept, since they only state how Codex's tools are called.
- 2026-10-26: design committed as final and pushed at the user's go-ahead ("Go for it"), before any measured run. The three trial files run side by side, each 3 runs at a time.
