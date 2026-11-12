# Does design knowledge help an agent design a futuristic bank app? (FUT-1)

**Status:** design, written 12 November 2026 before any measured run. Later changes go in the
[amendment log](#amendment-log). A small follow-up to [2026-11-design-factory](../2026-11-design-factory/) (DFX).

**Who built what:** an AI agent (Claude) wrote this design, the graders and the scripts. The user set the question, the
brief and the number of runs, and defined "futuristic" (below).

## Why

DFX gave an agent a Design Factory (OKF knowledge, 12 skills including Impeccable, a mandatory review) or nothing, on six
defined banking journeys. The factory was far ahead on completeness and accessibility checks, and the plain agent's
look was preferred. But those briefs named the journey. Here the brief is open: the agent has to decide **who the
users are, what they will need, and which features to build**. Two things could happen. Design knowledge could make the
agent's choices better grounded and more careful. Or it could pull it towards conventional banking and make it less
imaginative. This tests which.

The user's definition (12 November 2026): **"Futuristic is next generation app based on what they see as future needs of
future users."** The brief says exactly that and nothing more. What counts as "future" is each agent's own reading,
which is part of what is measured.

## Terms

As in DFX: Design Factory (the folder `factory/`, a snapshot of commit `bafa915`, unchanged), skill, OKF, storyboard,
axe-core. **Feature set**: the numbered features (F1, F2...) each run lists in `research.md`.

## Arms

| Arm | Workspace contains |
| --- | --- |
| **A. Plain agent** | a README saying this is Brindle Bank's design workspace. Nothing else. |
| **B. Design Factory** | the same, plus the factory, unchanged from DFX |

Agent: Codex CLI 0.167.1, hosted `gpt-5.6-luna`, medium effort, **web search live in both arms**, bubblewrap sandbox.
**One brief, 5 runs per arm: 10 runs.** Each agent does its own research; nothing is shared between runs. The factory is
frozen so this stays a clean replication on an open brief; fixing the factory's visual weakness is a different
experiment.

## The task (identical in both arms)

The prompt is in `scripts/make_trial.py` and `briefs/F1/prompt.md`. The agent is a designer at Brindle Bank (a fictional
UK bank) asked to design a futuristic version of the mobile app for a new generation of users. It must (1) research the
next generation of customers and the trends shaping mobile banking, with sources, in `research.md`; (2) choose the
features and list them as F1, F2... with the supporting finding and the frame that shows each; (3) create a storyboard
of 8 to 12 frames, each exactly 390 × 844 px, readable without a device mock-up and correct in a desktop browser 1280
px wide, each openable at `#frame-id`, listed in `screens.json`.

Changes from DFX, made because DFX showed they distorted the judging: the frame size and a 1280 px browser are
specified in the prompt, so no arm's frames get squeezed; judges see screens cropped to the phone interior from the
start. The prompt does not ask for demo controls. The factory's own skills still suggest them, which may count against
it, and that is a known cost of the frozen factory.

## Measures

**Primary, P1: blind pair preference on the whole design.** The 5 plain runs are paired with the 5 factory runs in all 25
combinations. Two vision-model judges (`google/gemini-4-argon`, `anthropic/claude-sonnet-5.5`) see the brief and two
unlabelled designs (cropped screens, up to 12 per design), in both orders. Criteria: overall, **novelty** (does it do
something a current banking app does not), **fit for a new generation of users**, **plausible as a UK bank's app**,
hierarchy, polish, identity. Pair score = share of the four votes for the factory (tie counts half).

**Test.** Run-level: take each run's mean score against the 5 runs of the other arm (so each run counts once), then a
permutation test swapping arm labels across the 10 runs (252 splits; two-sided; smallest possible p about 0.008).
Bootstrap 95% interval over runs. Because only 5 runs per arm exist, the test can detect only a large effect; a
non-significant result is "no difference shown", not "the same".

**Secondary (descriptive, not tested):**

- **S1 novelty and plausibility** from the criteria above, reported separately, because I expect them to pull
  apart.
- **S2 feature choice.** The features each run lists, coded by a model that sees only the list: which are real banking
  functions, which are gimmicks, and which are new; how many have a source; overlap between runs within an arm
  (Jaccard of coded feature categories). Each source URL is checked to be one the agent actually searched or opened
  (from the session log); a cited quote is checked against its page where fetched.
- **S3 research applied.** The H6 judge from DFX: share of the run's own features visibly present in its frames.
- **S4 accessibility.** axe-core violations per screen, control sizes. Exploratory; an open brief has no checklist.
- **S5 skill use**, from the Codex session log, as in DFX.
- **S6 cost**: tokens, time, list-price cost, with a token chart.

## Predictions (before any measured run)

The user's reason for the experiment: whether giving the agent design knowledge makes it better on an open brief. My
predictions, which I will state as predictions and not tune to:

1. P1 whole design: **no preference shown**, probably a lean to plain on novelty and identity.
2. Factory ahead on **plausible as a bank** and on S3/S4; plain ahead on **novelty**.
3. Factory runs converge on a more similar feature set than plain runs (lower variety).

## Pilot

One run of each arm on the brief (not part of the results), to check the rig, the contract (frames 390 × 844, openable
by id), the cost and that neither arm sits at a ceiling. Any change to the prompt or contract goes in the amendment log.

### Pilot result (12 November 2026, not part of the results)

Both runs delivered and met the contract (11 frames each, all open by id, all 390 px wide, all cropped cleanly). No
change to the prompt. Plain: 214 s, 205k tokens; factory: 496 s, 2,160k tokens. axe rule hits: plain 11, factory 0.
**What the two chose differed in kind.** The plain run built a spread of features (safe-to-spend, a week-ahead
horizon, connecting other accounts, an assistant, scenarios, a buffer, a payment check). The factory run spent 8 of
its 11 frames on one payment journey (purpose, payee, name check, warning, review, approval, unknown status, declined)
with a futuristic home and an assistant character, and said in its research to "keep everyday banking familiar". That
fits prediction 2 and prediction 3 (the factory narrows towards conventional, well-checked banking), from one run each.
Neither arm is at a ceiling.

## Impact, risks and recommendations

The report will say what the result means in practice, what risks it exposes, and give configuration recommendations
limited to the tested configuration, as DFX did. Model judges are not designers; a human vote on the same pairs is the
natural check and is not part of this design.

## Scripts

Copied from DFX and adapted where noted in the amendment log: `make_trial.py` (one brief), `setup.sh`, `verify.sh`,
`run_all.sh`, `run_pilot.sh`, `shoot.py`, `crop.py`, `sheet.py`, `judge_pairs.py`, `judge_research.py`, `skill_use.py`.
Still to write before the main run: the 25-pair judge with the new criteria and `analyse.py` (run-level permutation),
and the feature-coding script.

## Amendment log

(none yet)
