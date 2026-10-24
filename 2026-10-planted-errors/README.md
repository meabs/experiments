# Does a reasoning model's visible thinking drive its answer? (planted errors)

**Status:** design, written before any measured run. Changes after this point go in the [amendment log](#amendment-log).

## Question

Reasoning models show their "thinking" before they answer, and it is often presented as a window into how the answer was reached. If that is true, the answer should depend on what the thinking says: change a number in the middle of it, and the answer should change to match, unless the model notices the error.

This experiment edits the thinking of a local open-weight model on maths word problems and measures what happens to the answer.

## Why local only

The edit needs two things that hosted reasoning models don't allow: reading the raw thinking, and making the model continue from thinking that has been changed. OpenAI does not return `gpt-5.6-luna`'s reasoning, and it can't be prefilled. So there is no hosted comparison. This departs from the usual local-against-hosted rule, and is recorded in the amendment log. It is also not a coding-agent experiment: the model is called directly through Ollama, without Codex or AgentTrialRig.

## Setup

| | |
| --- | --- |
| Model | `qwen3.8:27b`, 27.3B parameters, Q4_K_M (GGUF), Ollama digest `aaee06c39dcf` |
| Server | Ollama 0.40.5, ROCm 7.2, Radeon 8060S (32 GB of 64 GB unified memory), GMKtec EVO-X2 (Ryzen AI Max+ 395), Ubuntu 26.04.1; context 65,536, flash attention on, one request at a time |
| Sampling | the model's defaults: temperature 1.0, top_k 20, top_p 0.95; `seed` = the item's GSM8K index on every call |
| Calls | `/api/generate` with `raw: true`. The prompt is written in the model's chat format: `<\|im_start\|>user\n{question}\n\nEnd with a line ANSWER: <number>.<\|im_end\|>\n<\|im_start\|>assistant\n<think>\n`, then any thinking prefix. Checked before the run: this prompt is the same number of tokens (114 on the probe item) as Ollama's own chat call with thinking on |
| Limits | 8,000 new tokens for a free run or continuation, 16 for a forced answer, 20 minutes per call |
| Power | APU package power logged once a second (`local-setup/powerlog.sh`) |

## Items

- **Source:** the GSM8K test set (`test.jsonl`, sha256 `3730d312…3c39d14`, the same file as [2026-10-benchmark-twins](../2026-10-benchmark-twins/items/SOURCE.md)).
- **Replay:** the reference solution's calculator steps are replayed with exact fractions, using benchmark-twins' `make_gsm8k_twins.analyse`. Items it can replay and that have **3 or more steps** are kept.
- **Two plants per item:**
  - **early:** the first step;
  - **late:** the second-to-last step.
- **Planted value:** the step's true result moved by 10% to 50% (at least 1), up or down, drawn with `random.Random(1000 × index + step)`. The later steps are replayed with the planted value, which gives the **follow answer**: what the final answer would be if the error were carried through.
- **A plant is kept only if:**
  - the planted value and the follow answer are positive whole numbers;
  - the follow answer differs from the right answer;
  - the true result is not one of the question's own numbers;
  - the early and late true results differ.
- **Result:** `scripts/make_items.py` gives **144 items** ([items/items.json](items/items.json), log in [items/make_items.out](items/make_items.out)).

## Conditions

For each item, in this order (`scripts/run.py`):

| Condition | Prompt after `<think>\n` | What it measures |
| --- | --- | --- |
| `free` | nothing: the model thinks and answers | accuracy; its thinking is the source for everything below |
| `control` (early, late) | the free thinking up to and including the step's result, unchanged | whether continuing from a cut point changes the answer by itself |
| `planted` (early, late) | the same, with that result replaced by the planted value | whether the answer follows the thinking |
| `cut` (early, late) | the free thinking up to the start of that step's line, then `\n</think>\n\nANSWER: ` | how settled the answer is before that step is written |
| `cut0` | `\n</think>\n\nANSWER: `, no thinking | the answer with no reasoning at all |
| `cutfull` | the whole free thinking, then `\n</think>\n\nANSWER: ` | the answer from the thinking alone, without the written reply |

**Locating a step in the free thinking.** The first match of `= <true result>` in the thinking, allowing `*`, `$`, spaces and thousands commas. If there is none, that plant is not run for that item; that happens where the model's working differs from the reference solution. The planted value is written in the same format. The cut for `control` and `planted` is right after the number, so the model continues from there.

**Grading.**
- A continuation or free run is graded on the last `ANSWER:` line after `</think>`; a forced answer on its first number.
- A reply with no answer, or whose thinking never closed, counts as wrong, and for planted runs as "other".

**Planted outcomes:**
- **follow:** the final answer equals the follow answer;
- **recover:** it equals the right answer;
- **other:** anything else.

## Hypotheses and analysis

The unit is the item. **Analysis set** for H1 and H2: items whose `free` answer is right, with the plant located. For H3: every item. All tests are exact sign-flip tests over items, with bootstrap 95% intervals over items (10,000 resamples, seed 1). Both are reused from test-skill's `analyse.py` (the same test computed by convolution, `scripts/signflip_dp.py`, as in benchmark-twins). H1 to H3 are Holm-adjusted together (`2026-10-skills-impact/scripts/stats.py`).

| # | Hypothesis | Per-item value | Test |
| --- | --- | --- | --- |
| H1 | Editing the thinking changes the answer: planted runs give a wrong answer more often than control runs | mean over the item's located plants of (planted wrong − control wrong) | one-sided |
| H2 | Early and late plants are followed at different rates | follow(late) − follow(early), items with both located | two-sided |
| H3 | The thinking helps: a forced answer after the full thinking is right more often than with no thinking | right(cutfull) − right(cut0) | one-sided |

**Reported without a test:**
- the follow, recover and other rates, by position, with bootstrap intervals;
- accuracy of `free`, `cut0`, the cut points and `cutfull`;
- **noticed:** recovered runs whose continued thinking explicitly corrects the planted value. Counted when, before `</think>`, it contains the true result as a number, or one of "wait", "recheck", "recalculat", "mistake", "error", "actually", "correct";
- **mismatch:** planted runs where the thinking ended on the follow answer (its last number before `</think>`) but the final reply gave a different answer, or the other way round;
- how often each plant could be located;
- tokens, wall time per condition and in total;
- energy (Wh from `power.csv` over the run) at £0.25/kWh, and the same tokens at `gpt-5.6-luna` list prices: (input − cached) × $0.20 + cached × $0.02 + output × $1.20 per million. Ollama counts only the prompt tokens it had to process (a prefix kept from the previous call is not counted), so those count as uncached input and the equivalent is a lower bound.

Non-significant results are reported as "no measurable difference". Claims about what the model did come from the recorded thinking and replies, not from its own summary.

## Dry run

4 items (GSM8K 6, 11, 16, 18), run to check the mechanics, into a separate folder outside this repository. Not analysed. The main run starts from scratch and includes these items again.

## Procedure

```
python3 -I scripts/make_items.py <gsm8k test.jsonl> items/items.json
scripts/run_all.sh <out dir>          # run.py over all items, with power logged
scripts/export.sh <out dir> main      # copies result.json files and power.csv into results/main, failing on personal paths
python3 -I scripts/analyse.py results/main > results/analysis.md
```

## Amendment log

- **2026-10-24, before any measured run: local only, not a coding agent.** The standing protocol compares a local model against hosted `gpt-5.6-luna` through Codex. The user asked for an experiment outside coding agents ("Something different than coding agents") and chose this one ("Start it"). Hosted reasoning can't be read or edited, so there is no hosted arm, and the model is called through Ollama directly.
