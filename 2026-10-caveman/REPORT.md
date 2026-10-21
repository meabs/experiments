# Report: does caveman cut tokens without losing correctness?

| | |
| --- | --- |
| Run | 2026-10-21, 36 runs, Codex (`gpt-5.6-luna`, high) only |
| Design | [README.md](README.md), with its amendment log |
| Data | [results/](results/): `analysis.md` (from `scripts/analyse.py`), the rig's `report.md`, and raw runs in `stage1/` |

## Answer

Caveman made Codex's output somewhat shorter and did not hurt correctness. Output is under 1% of the tokens a run uses, though, so the skill's promised "~75%" saving does not translate into a meaningful saving on the run. The total-token drop that was measured comes with fewer turns, not shorter replies, and its interval includes no saving at all.

## What was run

- **Arms.** `none`, and `caveman`: Matt Pocock's skill as it last shipped (commit `0a4b767`), invoked with `$caveman` at the start of the prompt. The skill is user-invoked only; the gate showed Codex loads it only through that prefix.
- **Tasks**, 6 runs each per arm:
  - `QA`: Experiment 3's eight "which classes are affected" questions, graded by F1 against truth taken from the compiled code;
  - `BUG` and `FEAT`: the skills-impact tasks and hidden tests.
- **Cursor.** The design planned a Cursor half. It was not run, because there were no Cursor credits; the decision was made before any Cursor run started.

## Results

| # | Hypothesis | Result | Verdict |
| --- | --- | --- | --- |
| C1 | Caveman cuts output tokens | 0.87 of `none` (95% CI 0.77 to 0.99) | Supported, narrowly |
| C2 | Caveman cuts total tokens by at least 20% | 0.84 (0.69 to 1.03); the rig's narrower interval, which treats the `none` mean as fixed, is 0.72 to 0.97 | Not supported under either interval |
| C3 | Correctness holds | 18/18 against 17/18 (QA F1 0.999 against 0.990) | Holds |

Points behind these numbers:

- **Output is too small to matter.** Output is 0.9% of a `none` run's tokens. Cutting it by 13% saves about 0.1% of a run, and almost all of a run is files and context sent again on every turn.
- **The total did fall, but not because of shorter replies.** Total tokens fell 16% (the point estimate), but caveman runs also took fewer turns (median 20 against 26). Each turn re-sends the whole context, so fewer turns is what moves the total. Whether caveman causes fewer turns, or this is noise, cannot be told from 18 runs; the interval includes 1.00.
- **Where the saving shows.** It is clearest on BUG (0.75, 0.61 to 0.94), and absent on FEAT (0.91, 0.58 to 1.37). Per-task results are exploratory.
- **Correctness.** The one failure was in `none`.
- **Cost.** About $2.50 at list prices.

## Measurement notes

- **The compression check could not separate the arms.** The design fixed this rule: a run counts as compressed if its final reply's rate of "a", "an" and "the" is under half the `none` median. With no skills, Codex's final replies already use almost no articles (a median of 0.0 per 100 words on QA, and 3.6 on BUG and FEAT). So the rule cannot separate the arms, and uptake rests on the gate (the prefix loads the skill) and on the rig's tool-use match (17/18).
- **Two intervals for relative cost.** The rig's interval treats the `none` mean as fixed. The interval in `analysis.md` also resamples the `none` runs, so it is wider and is the one used above.

## Limits

- One agent, one repository and three tasks, so the result says little about other tasks (see the skills-impact report on task clustering).
- The skill is user-invoked only, so this measures caveman when a user switches it on. The arm compares a prefixed prompt with an unprefixed one, and no control prompt carried a neutral prefix.
