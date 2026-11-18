# LRH: does long-running-agent scaffolding help a cheap model finish multi-session work?

Prompted by Anthropic's "Effective harnesses for long-running agents" (Justin Young, 26 Nov 2025). That
article reports no numbers. This measures the coding-agent half of it: structure that helps a fresh session
pick up where the last one stopped.

## Design

One agent builds `tasks.py` (a 12-feature CLI task manager, `spec/SPEC.md`) across up to 8 short sessions.
A session ends when the agent stops calling tools, uses its turn cap, or its context passes a cap. The next
session starts with an empty conversation; only the working directory (files and git) carries over. The agent
may call `declare_done`, which ends the run. A hidden test per feature (`hidden/`, never visible to the agent)
decides what passes. The reference solution (`reference/tasks.py`) passes all 12.

Four conditions, each adding one component to the one before. The model, tools, spec and limits are identical.

| Condition | Adds |
|---|---|
| `bare` | Only the task prompt, SPEC.md, and a git repo |
| `notes` | Read git log and PROGRESS.md at start; commit and append progress notes at the end |
| `featurelist` | `feature_list.json` (all `passes: false`); one feature per session; only `passes` may be edited |
| `full` | `init.sh` startup check run each session; write a test per feature before setting `passes: true` |

Model: `qwen/qwen3.7-flash` on OpenRouter, temperature 0.7. Two context regimes, set after the pilots below:

- **tight**: 12 tool turns and a 10,000-token context per session, 8 sessions.
- **loose**: 25 tool turns and a 20,000-token context per session, 6 sessions.

## Pre-registered outcomes (written before the main runs)

- **Primary:** features passed out of 12 at the end of the run, per condition and regime, with a bootstrap 95%
  interval. Differences are between neighbouring conditions (each adds one component), and `full` against `bare`.
- **Secondary:** premature victory (declared done with fewer than 12 passing), sessions ending with a broken
  program (add then list fails), cost per run, forbidden edits to `feature_list.json`, and features marked
  passing that fail the hidden tests.
- Runs that error out are excluded and counted. A run stopped by the budget cap is excluded.

## Limits (known in advance)

- One cheap model. Results say nothing about the frontier models the article used.
- One small app. The feature list is supplied, so the article's initializer agent is not tested.
- The context and turn caps are my choice, and the answer depends on them: the pilots showed that without
  them, every condition finishes inside one session.
- Hidden tests are mine. F04 (ids never reused after a delete) was the one feature the pilot runs missed.

## Pilots (not part of the results)

- `runs/_pilot1_easy`: 40 turns, 32k context, 6 sessions, one run per condition. Scores: bare 11, notes 11,
  featurelist 12, full 12. All four had 11 to 12 features working after session 1, so sessions did not matter.
  The limits above were tightened because of this.
- `runs/_pilot2_tight`: the tight regime, one run each. Scores: bare 11, notes 9, featurelist 10, full 5. In
  `full` every session hit the context cap while still on the startup routine. One run each, so noise.

## What changed from the plan (disclosed)

- **30 runs per condition and regime, not 20.** I topped up with reps 21 to 30 to even out runs lost to errors.
- **Errors.** In the first 160 runs, 27 ended with HTTP 400 from OpenRouter (not tied to a condition: tight 5, 5, 4, 3
  across bare, notes, featurelist, full; loose 4, 2, 0, 4). Cause, found from the response body: the model sometimes
  writes tool-call arguments that are not valid JSON, and the harness echoed them back, which the provider rejects.
  I fixed the harness (bad arguments are replaced with `{}` and the agent is told its call was invalid) and reran
  every errored run (`--redo-errors`). The tables below have 0 errors. The unchanged harness would have dropped
  the runs where the model produced the worst output.
- The analysis script gained an exact test for yes/no outcomes after the first loose results were in. Those
  tests are unadjusted and exploratory.

## Results (qwen/qwen3.7-flash, 240 runs, $3.64 in total including pilots and reruns)

Mean features passed out of 12, with a bootstrap 95% interval, 30 runs per cell:

| Condition | Tight (10k context, 12 turns) | Loose (20k context, 25 turns) |
|---|---|---|
| bare | 10.27 (9.27 to 10.97) | 11.27 (10.40 to 11.80) |
| notes | 10.07 (8.80 to 11.07) | 10.97 (10.03 to 11.57) |
| featurelist | 7.90 (6.60 to 9.17) | 9.93 (8.83 to 10.87) |
| full | 9.03 (7.97 to 10.03) | 10.63 (10.03 to 11.10) |

Differences in the mean (each condition minus the one before), 95% interval:

| Step | Tight | Loose |
|---|---|---|
| notes − bare | −0.20 (−1.67 to +1.20) | −0.30 (−1.37 to +0.80) |
| featurelist − notes | **−2.17 (−3.80 to −0.43)** | −1.03 (−2.33 to +0.30) |
| full − featurelist | +1.13 (−0.53 to +2.73) | +0.70 (−0.43 to +1.93) |
| full − bare | −1.23 (−2.50 to +0.17) | −0.63 (−1.50 to +0.37) |

Declared done with fewer than 12 passing ("premature victory"), and reached 12 of 12:

| Condition | Premature, tight | Premature, loose | Reached 12/12, tight | Reached 12/12, loose |
|---|---|---|---|---|
| bare | 0/30 | 1/30 | 7/30 | 19/30 |
| notes | 0/30 | 0/30 | 12/30 | 16/30 |
| featurelist | 1/30 | 7/30 | 2/30 | 11/30 |
| full | 0/30 | 14/30 | 4/30 | 6/30 |

What I take from it:

- **Nothing I added beat the bare prompt on mean features passed.** In both regimes `bare` has the highest mean, and
  no step up the ladder has an interval that excludes zero on the positive side.
- **The feature list cost something in the tight regime** (−2.2 features against `notes`). I did not test why. My
  guess is the extra files to read and update use up a small context, but that is a guess.
- **In the loose regime, `full` declared victory early in 14 of 30 runs, against 1 of 30 for `bare`** (exact test
  p < 0.001, and it survives a Bonferroni correction over the 16 yes/no tests I ran). It also reached 12 of 12 in 6 of
  30 runs against 19 of 30 (p = 0.001). The article describes premature victory as a problem the structure
  fixes; here the full structure was where it showed up most. In those 14 runs the most-missed feature was F12 (undo,
  10 of 14). I then checked their work directories. The agents' own tests passed in all 14 of those runs (and in
  all 16 other `full` runs), so passing your own tests does not separate the groups. Their tests mentioned undo in
  3 of 14 runs against 8 of 16 for the rest (small numbers). Most of those agents declared done while their own
  `feature_list.json` still showed most features as not passing: on average about 5 of 12 were marked passing, and
  only 1 of the 14 had marked all 12. So the failure looks like ignoring the list when deciding to stop, not being
  fooled by green tests. That is read from the final state of the files, not from why the agent decided.
- **`featurelist` against `notes` on premature victory** (7/30 against 0/30, p = 0.011) does not survive that
  correction.
- **Premature victory was rare outside those conditions.** Agents without a feature list mostly ran out of sessions
  without calling `declare_done`, so the failure the article describes could barely occur there.
- Forbidden edits to `feature_list.json`: 0 in all 120 runs that had one. Features marked passing that fail the
  hidden tests: 6 runs in total (3 `featurelist`, 3 `full`, all in the loose regime), one feature each.

## A small check with a stronger model (anthropic/claude-haiku-5.5, added after the main results)

Not pre-registered, and small (5 to 6 runs per cell), to see whether the qwen pattern carries over. Loose limits
(25 turns, 20k context).

| Condition | n | Mean features passed | Reached 12/12 | Declared done with <12 | Sessions used | Cost per run |
|---|---|---|---|---|---|---|
| bare | 6 | 11.83 | 5 | 1 | 1.0 | $0.015 |
| featurelist (14 sessions) | 5 | 10.20 | 4 | 1 | 10.0 | $0.065 |
| full (14 sessions) | 5 | 12.00 | 5 | 0 | 9.6 | $0.070 |

- **Haiku did what the harness said, qwen mostly did not.** Told to do one feature per session, it did, so it
  needed about 10 sessions. qwen's median biggest single-session gain was 9 to 10 features.
- **My first Haiku batch had a design flaw.** I gave `full` 6 sessions, and one feature per session caps the score at
  6 of 12. Five of six runs scored exactly 6. That was my session budget, not the agent. I reran `featurelist` and
  `full` with 14 sessions (the table above). The 6-session `full` runs are in `runs/anthropic_claude-haiku-5.5-loose-full-*`
  and `bare` finished everything in one session, so its session cap never mattered.
- **For this model and task the structure made no difference to the score and cost four to five times as much.**
  `bare` finished 12 of 12 in one session in 5 of 6 runs. The scaffolded versions matched that, using about 10
  sessions. This task fits in one session for Haiku, so there was nothing for the scaffold to rescue. A task that
  does not fit in one session for a stronger model is the test the article describes, and I have not run it.
- The qwen runs are not affected by the cap: their feature-list agents mostly ignored one-feature-per-session.

None of this says the article is wrong. It used a much stronger model, a much bigger project, a browser test loop
and a model-written feature list; this used a cheap model, a 12-feature CLI and a supplied feature list. It says
that, for this cheap model on this task, the structure did not help on the score and one version of it made
early declarations of victory more common.

## Files

Each run folder under `runs/` has `result.json` (scores, per-session detail, cost), `transcript.jsonl.gz` (every
model turn and tool result; gzipped to save space) and `work/` (the final working directory). `runs/ledger.jsonl`
records the cost of every model call.


`harness.py` runs experiments, `analyze.py` summarises them, `test_harness.py` tests the harness with a scripted
fake agent (`python3 -m unittest test_harness`), `hidden/` holds the tests that score runs.

```
python3 harness.py --model qwen/qwen3.7-flash --regime tight --reps 20 --max-sessions 8 --max-turns 12 --ctx 10000 --workers 6
python3 analyze.py --model qwen_qwen3.7-flash-tight
```
