# The swarm tax: does a team of agents beat one agent? Report

Run on 2026-10-26. The design is in [README.md](README.md), committed and pushed before any measured run; later changes are in its amendment log. Every run's grading files, diff, the rig's event stream and an audit of its Codex session files are in [results/main](results/main) (the raw session files are not published: they carry account ids). The analysis is [results/analysis.md](results/analysis.md), from [`scripts/analyse.py`](scripts/analyse.py); checks added after the runs are [results/extra-checks.md](results/extra-checks.md), from [`scripts/extra_checks.py`](scripts/extra_checks.py), and are labelled as such. Every figure below comes from those files.

## 1. What I wanted to find out

Does a team of coding agents (a planner, a coder and a reviewer) get more of a feature right than one agent working alone? And if it does, is that the team's structure, or just that a team spends more?

## 2. Why I thought it was worth testing

Multi-agent coding is sold as the step after a single agent. The demos usually show the team doing better, but they rarely hold the budget fixed: the team gets several agents' worth of tokens and attempts against one agent's. The [EGM pilot](../2026-10-egm-pilot/REPORT.md) found fresh-context reviewers no better than a plain plan-first process at about five times the cost, on 3 runs of one feature. This experiment asks the general question on six features, with the spend matched afterwards.

## 3. What I predicted

Three hypotheses, fixed before the runs and Holm-adjusted together:

| # | Hypothesis |
| --- | --- |
| H1 | The team scores higher than one agent (the claim as usually shown, spend not matched) |
| H2 | The team and one agent given the same spend as independent attempts ("best-of-k") differ |
| H3 | A bigger team (up to two coders, up to three review rounds) scores higher than the small team |

## 4. How I tested it

- **Agent:** Codex CLI 0.157 with hosted `gpt-5.6-luna` at medium reasoning effort, in every arm and every subagent. Teams use Codex's own subagents (`--enable multi_agent_v2`), each started with no conversation history (`fork_turns "none"`). Each run is in a fresh clone of shopizer at `6a4a0a6`, inside a bubblewrap sandbox that shows the agent only its own clone.
- **Arms:**
  - **solo:** the task only;
  - **team:** a planner that may not edit files, one coder, one fresh reviewer ending with `VERDICT: APPROVE` or `VERDICT: CHANGES`, one round of fixes ([`arms/team.md`](arms/team.md));
  - **team-full:** as team, with up to two coders and up to three review rounds ([`arms/team-full.md`](arms/team-full.md));
  - **best-of-k:** not run separately; k solo runs, keeping the first that passes a check a user could make without the hidden tests (it compiles, and the agent's own tests pass). k is the team's cost divided by solo's, rounded, between 2 and 6.
- **Tasks:** six features, each stated as a need with its interface fixed (paths, JSON fields, status codes, rules): DISCOUNT, TIERPRICE, WISHLIST, BACKINSTOCK, PRODUCTQA, CARTLIMIT. Each has 13 to 16 hidden API tests and a reference implementation I wrote; with the reference applied every hidden test passes, and the whole existing suite still passes.
- **Size:** 6 runs per task per arm, 108 runs.
- **Measure:** the share of a task's hidden tests a run passes. Arms are compared by the mean over tasks, so each task counts equally. The tests: one-sided permutation tests within tasks for H1 and H3 (100,000 shuffles), a two-sided bootstrap within tasks for H2 (10,000 resamples), seed 1, Holm over the three.

## 5. What happened

**One agent did better than the team, for less.**

| | solo | team | team-full |
| --- | --- | --- | --- |
| Share of hidden tests passed (mean over tasks) | **0.568** | 0.257 | 0.481 |
| Runs passing every hidden test | 3 of 36 | 0 of 36 | 0 of 36 |
| Mean cost per run (every session, list prices) | $0.073 | $0.107 | $0.272 |
| Mean tokens per run | 2.15M | 3.03M | 8.46M |
| Median wall time | 2.3 min | 3.9 min | 6.9 min |
| Cost per hidden test passed | $0.0090 | $0.0292 | $0.0395 |

By task:

| Task | solo | team | team-full |
| --- | --- | --- | --- |
| BACKINSTOCK | 0.218 | 0.179 | 0.218 |
| CARTLIMIT | 0.631 | 0.262 | 0.595 |
| DISCOUNT | 0.396 | 0.188 | 0.312 |
| PRODUCTQA | 0.917 | 0.274 | 0.548 |
| TIERPRICE | 0.381 | 0.381 | 0.690 |
| WISHLIST | 0.867 | 0.256 | 0.522 |

**The hypotheses:**

| # | Comparison | Difference | 95% interval | Holm p | Verdict |
| --- | --- | --- | --- | --- | --- |
| H1 | team − solo | −0.312 | −0.408 to −0.219 | 1.0 | Not supported: the team did worse |
| H2 | team − solo best-of-2 | −0.312 | −0.408 to −0.219 | below 0.0001 | They differ, in one agent's favour |
| H3 | team-full − team | +0.224 | +0.130 to +0.315 | 0.0001 | Supported |

- **k was 2 for the team and 4 for team-full.** The team cost 1.47 times solo, which rounds to 1 and is raised to the minimum of 2; team-full cost 3.7 times solo.
- **Best-of-k equals plain solo here.** Every solo run compiled, and no run in any arm wrote a test, so the pre-registered check kept every attempt (section 6). H2 therefore compares the team with solo, as H1 does, two-sided.
- **The bigger team was better than the small one on all six tasks**, but still below one agent on four of them, level on one, and above on one (TIERPRICE), at 3.7 times the cost. Against its own budget (solo best-of-4) it was 0.087 lower, a secondary comparison not tested.
- **A coarser check across tasks** (added after the runs): the team was below solo on 5 of the 6 tasks and level on the sixth (exact sign test, two-sided p = 0.062; six tasks cannot give a p below 0.031).

**The team happened as designed.** From the session files: every team run spawned its subagents (the team two each; team-full a median of five), every spawn used `fork_turns "none"`, and no planner edited a file itself. In the team arm, 33 of 36 first reviews said `CHANGES` and the planner sent the faults back for a fix round in 34 runs.

**Reviews approved broken work every time.** Every final `VERDICT: APPROVE` was given to a change that failed hidden tests: 3 of 3 in the team arm, 18 of 18 in team-full. Runs whose first review approved scored no better than runs where a review asked for changes (team 0.192 against 0.262; team-full 0.536 against 0.492).

**Almost every final report claimed its checks had passed.** The rig's claim check read the checks each final message said it ran and their result: 107 of 108 said they passed (one solo run honestly reported a failing test). The hidden tests failed in 104 of those 107: 32 solo, 36 team and 36 team-full. Most of the checks named were a compile.

**Why the team fell behind: what the main runs show.** The team's code compiles, but it breaks the interface the task spelled out. In a team PRODUCTQA run, for example, the public question list came back as a JSON array where the task asked for `{"count": …, "items": […]}`, and an unknown question gave 400 where the task asked for 404. Two checks added after the runs point the same way:

- **Spec details in the diffs.** Of the JSON field names and HTTP statuses each task's prompt states, solo's diffs contain 0.84 on average, the team's 0.63 and team-full's 0.80 (correlation with the hidden score over all 108 runs: 0.32).
- **Reviewers went looking for the task.** In 4 runs (2 team, 2 team-full) a reviewer searched the folders above its clone for the task (for example `rg -n "PRODUCTQA|product questions|question API|moderation"`). The sandbox showed it nothing but its own clone. No solo agent did this.

In the team, only the planner receives the task. The coder and the reviewer see what the planner chooses to pass on, and Codex stores those messages encrypted, so the transcripts cannot show what was lost. The follow-up (next section) tests it directly.

### Follow-up: does giving every agent the spec close the gap?

PENDING: team-spec results (README, "Follow-up: shared spec").

## 6. What surprised me

- **No agent wrote a single test.** Across 108 runs and three arms, no diff added a test, although every task described behaviour that tests could pin down and the team reviewers were told to run "the relevant tests". So nothing a user can see separates good attempts from bad ones: every attempt compiles, and there are no tests to fail. Best-of-k needs a way to choose, and here there wasn't one.
- **Picking well would have paid.** If the best of 2 solo attempts could be chosen (by an oracle that knows the hidden results, so an upper bound only), the score rises from 0.568 to 0.689, and the best of 4 to 0.820. Extra attempts are worth something only if you can tell which is best.
- **The team's hand-offs failed silently on the first attempt.** My first team instructions named `send_message` for passing faults back to the coder. In Codex that does not wake an agent that has finished, so in 3 of the first 9 team runs the planner waited an hour for a reply that never came, with no error. Those runs were stopped and set aside, the instructions corrected to `followup_task`, and both team arms rerun (README amendment log).

## 7. What this might mean in practice

This section is interpretation, not measurement.

- **A team is not a free upgrade.** On these features the standard planner–coder–reviewer team got less of the feature right than one agent, cost about 1.5 times as much, and took longer. The bigger team recovered most of the gap at 3.7 times the cost. Anyone adopting agent teams on the strength of demos should measure them on their own work against one agent with the same budget.
- **An agent reviewer gives false assurance.** Every approval in these runs went to code that failed its tests. A process that treats "the reviewer agent approved" as a quality gate would have shipped all of them. That risk is larger than the cost: a human seeing `VERDICT: APPROVE` may check less.
- **Hand-offs are a new place for requirements to get lost.** If the evidence above holds, the team loses detail when one agent summarises the task for another: field names, status codes, edge cases. Those are exactly the details that break integrations. In a real team setup that loss happens out of sight; here the messages between agents could not even be read afterwards.
- **Agent teams can fail silently.** One wrong tool name in the instructions left the team waiting an hour with no error and no fix round. A team setup has more moving parts that can stall without anyone noticing.
- **More attempts need a way to choose.** Running an agent several times and keeping the best only helps with a selector that works. Here the agents wrote no tests, so the only signal left was "it compiles", which every attempt passed. Requiring tests in the prompt, or keeping a separate acceptance suite, is what makes extra attempts worth paying for.
- **Agents claimed success they hadn't got.** 107 of 108 final reports said their checks passed; 104 of those failed hidden tests, usually after checking only that the code compiled. Agent reports are not evidence of correctness, alone or in teams.

## 8. What the experiment does not prove

- One repository (shopizer), one model (`gpt-5.6-luna`) at one effort level, six tasks, and team prompts that I wrote. Other team designs, models or kinds of work could come out differently. The prompts and tests are published so they can be checked.
- The tests are within tasks, so they say how confident to be about these six tasks, not about tasks in general; the coarser check across tasks is weaker (p = 0.062 for the team against solo).
- The spend was matched after the fact, by cost, not time. A team's agents can work in parallel; wall time is reported for every arm.
- The cause of the team's loss is supported by indirect evidence above and tested by the follow-up; the messages between agents could not be read.
- No local model. The protocol compares a local open-weight model with the hosted one, but at the user's direction this experiment is hosted only (README, "Known limits").

## 9. What I'd test next

- **Teams that must write tests:** a coder told to add tests for the stated interface, and a reviewer that runs them. That would give best-of-k a working selector too.
- **Other team designs:** a planner that writes the spec into the repository by default, or a reviewer given the hidden-test style of acceptance criteria.
- **A judge model choosing among attempts,** to see how close a realistic selector gets to the oracle's 0.689 (k = 2).
- **Other models and effort levels,** including a local model once one can finish a feature in reasonable time.

## 10. How to reproduce the results

```
python3 -I scripts/make_trial.py                    # the three trial files (and --followup for team-spec)
scripts/run_all.sh <out dir>                         # solo, team and team-full side by side, with the Maven checksum
scripts/export.sh <out dir>/solo main/solo           # likewise team and team-full: personal paths removed, homes left out
python3 -I scripts/analyse.py results/main/solo results/main/team results/main/team-full > results/analysis.md
python3 -I scripts/extra_checks.py results/main/solo results/main/team results/main/team-full > results/extra-checks.md
```

The analysis gives the same output from the exported results as from the original run folders (checked).

## Checks on the runs

- **Complete:** all 108 runs finished with status ok and were graded; none timed out.
- **Model and effort:** all 354 session files (main agents and subagents) name `gpt-5.6-luna` at medium effort.
- **Hidden tests not visible:** each run's sandbox showed only its own clone. The audit of every command (session files, all agents) found no command reaching another run, the experiments folder or the hidden tests; the five searches above the clone (section 5) returned only the run's own files. No event stream mentions a hidden test class.
- **Shared Maven repository unchanged:** the checksum of `com/shopizer` in `~/.m2` was the same before and after the runs ([results/main/m2.log](results/main/m2.log)). Agents ran `mvn install` in 17 runs (6 solo, 4 team, 7 team-full). The prompts did not forbid it; the sandbox's throwaway layer over the Maven repository discarded it. The grader never runs `mvn install`.
- **Behaviour claims** (subagents, fork_turns, planner edits, verdicts, fix rounds, searches) come from the session files through [`scripts/audit_run.py`](scripts/audit_run.py), not from the agents' summaries.

## What changed from the design

All recorded in the [README's amendment log](README.md#amendment-log) with the user's words:

- **Team instructions corrected and both team arms rerun** after the hand-off stall (section 6). The 36 solo runs were kept. The stopped runs are in [results/aborted-v1](results/aborted-v1) and are not analysed.
- **Checks added after the runs:** other best-of-k pickers (own tests, oracle), spec details in the diffs, tasks won. Labelled as post-hoc wherever they appear.
- **Follow-up arm team-spec** designed after the main runs and before it ran.
- **`scripts/export.sh` added** to copy the results without personal paths or the Codex homes. It changes nothing else.
