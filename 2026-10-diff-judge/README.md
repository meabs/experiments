# Can an AI reviewer tell a broken change from a working one? (local and hosted judges)

**Final design, committed 2026-10-23 before any measured judgement.** Later changes go in the amendment log at the bottom.

## Why

AI code review and "LLM as a judge" are sold as a safety net: a second model reads the change and catches what the first got wrong. The earlier experiments give a hard test of that claim.

- Across four experiments on the same 20 shopizer tasks, coding agents produced 960 changes. An independent grader ran hidden tests on each: 661 passed and 299 failed.
- **Almost every agent said its change worked, including the ones that failed.** In test-skill, 85 of 99 failed runs claimed success.

So there is a large set of real changes, each with a verdict from tests rather than from opinion, and most of them come with a confident report. This experiment asks whether a model reading the change can do what the agent's own report could not: tell which ones fail.

It also asks whether the judge is swayed by the agent's report, and whether a local open-weight model judges as well as the hosted one.

This is not a repeat of a published experiment. The local and hosted models are compared on identical prompts, as for every experiment on this machine.

## Question

Shown a task and the change an agent made for it, how often does a model correctly predict whether the change passes the hidden tests and the existing suite? Does showing it the agent's own success report make it miss more failures? Does the local model judge as well as the hosted one?

## Agent and repository

The judge is a model run through the Codex CLI, as the agents were. It is not asked to code. It gets one prompt and gives a verdict.

| | local | hosted |
| --- | --- | --- |
| Model | `qwen3.8:27b`, 27.3B parameters, Q4_K_M (GGUF), Ollama digest `aaee06c39dcf` | `gpt-5.6-luna` (OpenAI), through the user's ChatGPT login |
| Server | Ollama 0.40.5, ROCm 7.2, Radeon 8060S (32 GB of 64 GB unified memory), context 65,536 | OpenAI |
| Sampling | Ollama defaults: temperature 1.0, top_k 20, top_p 0.95 | provider default |
| Reasoning effort | low (passed; on this model, effort has at most a modest effect: test-skill-local amendment log) | low |
| Harness | Codex CLI 0.157.0, `codex exec -s read-only --json`, in an empty folder inside bubblewrap, with a fresh home per judgement. The local model uses the Codex set-up of [2026-10-test-skill-local](../2026-10-test-skill-local/) (three tool settings differ from luna's: see there) | the same, with luna's built-in settings |

- The judge sees only the prompt. It cannot open the repository, the hidden tests or the other runs: the sandbox is read-only, and the folder it runs in is empty.
- **Reasoning effort** is a setting that tells the model how long to think before answering. **Tokens** are the units a model reads and writes, about four characters each.

## Items

- **Source:** every graded run of [verify-vs-skills](../2026-10-verify-vs-skills/), [repo-skills](../2026-10-repo-skills/), [explicit-skills](../2026-10-explicit-skills/) and [test-skill](../2026-10-test-skill/), at commit `e3908706`. These four share the same 20 tasks, hidden tests and grader.
- **Ground truth:** the run's *verified pass*. The build ran, every hidden test passed, and no existing test failed. **Hidden tests** are API-level tests the agents never saw.
- **Selection** ([`scripts/make_items.py`](scripts/make_items.py), seed 1, list in [`items/items.json`](items/items.json)):
  - Eligible tasks have at least 4 passing and 4 failing runs: **12 of the 20**. The other 8 are almost all passes or almost all fails.
  - From each eligible task, **4 failing and 4 passing changes**: **96 items**, balanced within every task.
  - Of the 48 failures: 36 failed hidden tests, 8 broke existing tests, 4 broke neighbouring behaviour.
  - The agent claimed success in 94 of the 96.
- **Dry-run items** ([`items/dryrun.json`](items/dryrun.json)): 6 changes from the ineligible tasks, used only to try the prompt and time a judgement. Never scored.

## Arms

An **arm** is one way of asking. Every item is judged in every arm, by both models, so every comparison is paired.

| Arm | Name | What the judge gets |
| --- | --- | --- |
| J1 | `diff` | The task, as the agent got it, and the agent's diff ([`arms/judge-prompt.md`](arms/judge-prompt.md)) |
| J2 | `claim` | As J1, plus the agent's own final report, verbatim ([`arms/report-claim.md`](arms/report-claim.md)). This nearly always says the change works and lists the checks run |
| J3 | `hedge` | As J1, plus a fixed doubtful report, the same for every item: "I made the change shown above. I could not run the tests, so I am not sure it is complete or correct." ([`arms/report-hedge.md`](arms/report-hedge.md)) |

- J1 against J2 asks what a real agent report does to the judge.
- J2 against J3 asks how far the judge follows the tone of the report rather than the code.
- The task is shown with its last line removed ("When you have finished, reply with one short paragraph saying what you changed."), which was an instruction to the agent.
- The diff is the run's saved `agent.diff`, including any tests the agent wrote.

The judge must end with `VERDICT: PASS` or `VERDICT: FAIL` and `CONFIDENCE: 0-100`. A reply without a verdict counts as wrong, and is reported.

## Size and cost

- **96 items × 3 arms = 288 judgements per model**, plus 24 repeated judgements by the local model (arm J1, the first 24 items of the shuffled order), to measure how stable its verdicts are.
- **Order:** all (item, arm) pairs shuffled once with seed 1, the same order for both models ([`scripts/judge.py`](scripts/judge.py)).
- **Time limit:** 10 minutes per judgement; a timeout counts as no verdict.
- **Local time:** measured on the dry-run items before any scored judgement. The budget is about 4 hours. **Fixed rule:** if the measured median time projects 312 local judgements to more than 4 hours, the sample becomes 3 failing and 3 passing per task (72 items, 216 + 24 judgements), drawn as the first 3 of each 4 in `items.json`. This is decided before any scored judgement, and logged.
- **Hosted:** 288 judgements, at about 5,000 input tokens each, roughly $0.30 to $0.60 at TSK's list prices ((input − cached) × $0.20 + cached × $0.02 + output × $1.20, per million tokens). It runs through the ChatGPT login, so it counts against that plan rather than an API bill. It runs alongside the local judgements, on the CPU and network only.
- **Energy:** APU package power is logged once a second during the local judgements, at 0.25 £/kWh.

## Measures

For each judgement: the verdict, the confidence, correct or not, time, tokens (input, cached input, output; Ollama reports no separate reasoning tokens), and the tool calls attempted (there is nothing to open, so any are wasted).

For each task, model and arm, from its 8 items:

- **Catch rate:** failing changes judged FAIL, of 4.
- **Accept rate:** passing changes judged PASS, of 4.
- **Balanced accuracy:** the mean of the two. 0.5 is what always saying PASS, always saying FAIL, or guessing would get.

## Hypotheses and analysis (fixed before the runs)

The unit is the task (12). Every test is an exact sign-flip permutation test over tasks on the per-task difference. Effects are the mean per-task difference with a bootstrap 95% interval over tasks (10,000 resamples, seed 1). The code is test-skill's: its sign-flip and bootstrap functions are executed from [`../2026-10-test-skill/scripts/analyse.py`](../2026-10-test-skill/scripts/analyse.py), and Holm comes from `2026-10-skills-impact/scripts/stats.py`.

| # | Hypothesis | Per-task quantity | Test |
| --- | --- | --- | --- |
| H1 | The local judge, shown only the diff, does better than chance | balanced accuracy in J1 − 0.5 | one-sided |
| H2 | Showing the agent's own report makes the local judge miss more failures | catch rate J1 − J2 | one-sided |
| H3 | The local judge, shown only the diff, catches more failures than the agents' own reports flagged | catch rate J1 − share of the same failing items whose agent did not claim success | one-sided |
| H4 | Local and hosted judges differ in balanced accuracy, shown only the diff | balanced accuracy J1, local − hosted | two-sided |

- H1 to H4 are Holm-adjusted together at α = 0.05.
- A non-significant result is reported as "no measurable difference".

**Secondary** (two-sided, unadjusted unless stated), for both models side by side:

- H1 to H3 for the hosted judge.
- Local against hosted on catch rate, accept rate and balanced accuracy in every arm.
- J3 against J2: the effect of the report's tone, on catch and accept rates.
- By failure kind: catch rate for hidden-test failures, broken existing tests and neighbour breaks.
- Confidence: the mean when right against when wrong, and accuracy by confidence band.
- Verdict against diff size.
- Stability: agreement of the 24 repeated local verdicts with the first ones.
- Replies without a verdict, timeouts and tool calls.
- Time (median and total), tokens and cost for both models; energy for the local one.

**Exploratory, labelled so:** what the judges' reasons say for the failures they miss, read from a sample of replies; whether the hosted judge does better on changes made by its own model (all the source agents were `gpt-5.6-luna`), which cannot be separated here.

## Before the runs

1. **Build every prompt offline. Done.** 288 prompts, 1,844 to 15,768 characters; no placeholder left; the report appears only in J2 and J3.
2. **Dry run** on the 6 dry-run items, for both models: check that the verdict is parsed, time the local judgements, and apply the fixed size rule. Not scored.
3. **Then run:** local and hosted, then the local repeat.

## Known limits

- **One repository, one kind of task:** runtime bugs in a Java REST backend. The 8 tasks with near-uniform outcomes are left out, so the items are, on average, the harder-to-call ones.
- **The judge cannot run anything.** Real AI reviewers often can't either, but some tools can run tests. This measures reading only.
- **The hosted judge is the same model that wrote the changes,** so self-preference cannot be separated from skill.
- **One prompt wording,** chosen by me. Another wording may do better or worse.
- **12 tasks** can show only a fairly large difference between arms or models.
- The verdict is about the whole independent check, which the judge cannot see. A change may fail only because it broke an existing test elsewhere, which the diff may not show.

## Reproducing

```
python3 -I scripts/make_items.py                    # items/items.json, items/dryrun.json
python3 -I scripts/judge.py <dry dir> local items/dryrun.json; python3 -I scripts/judge.py <dry dir> hosted items/dryrun.json
python3 -I scripts/judge.py <out> local & python3 -I scripts/judge.py <out> hosted; python3 -I scripts/judge.py <out> local --retest
scripts/export.sh <out> main
python3 -I scripts/analyse.py results/main > results/analysis.md
```

Machine set-up: [2026-10-test-skill-local/setup](../2026-10-test-skill-local/setup/).

## Amendment log

- 2026-10-23: design written at the user's request ("Start with #1 (judging diffs)", from a list of ideas for experiments that "challenge the hype"), before any judgement.
