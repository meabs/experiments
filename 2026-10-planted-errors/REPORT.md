# Does a reasoning model's visible thinking drive its answer? (planted errors): report

Run on 2026-10-24. The design and hypotheses are in [README.md](README.md), committed and pushed before the measured run. Every call's prompt cut point and output are in [results/main](results/main/). The analysis is in [results/analysis.md](results/analysis.md), from `scripts/analyse.py`.

## Summary

- **The thinking does real work.** Forced to answer with no thinking, the model got 33 of 144 problems right (23%). Forced to answer after its full thinking, it got 135 (94%). Midway through, the answer was still forming: 23% right before the first step was written, 57% before the second-to-last.
- **A wrong number planted in the thinking changed the answer about a third of the time.** Across 230 planted errors (on problems it had got right), the model carried the error through to the matching wrong answer in 81 (35%). Continuing from the same points with the thinking unchanged gave a wrong answer in 1 of 230.
  - **H1 is supported:** planted runs were wrong 37 points more often than control runs (95% interval +30 to +44, Holm p < 0.001).
  - **H2 is supported:** errors planted late were followed more often than early ones (41% against 30%, +13 points per item, Holm p 0.047).
  - **H3 is supported:** the full thinking raised accuracy by 71 points over no thinking (Holm p < 0.001).
- **When it followed an error, it did so with confidence.** In 74 of the 81 followed runs the thinking showed no sign of doubt, and 80 of the 81 replies showed none.
- **It caught most slips, but not reliably.** In 124 of the 230 runs (54%), it noticed the planted number in its thinking, recomputed the step and recovered.
- **In 23 runs (10%), the thinking and the answer disagreed.** The thinking finished on the wrong answer that follows from the error, sometimes after "double-checking" it. The written reply then redid the working and gave the right answer. The reverse never happened (right thinking, wrong reply: 0).
- **Cheap to run:** 1,143 calls, 1.71 hours on this machine, 145 Wh of package power (£0.04 at £0.25/kWh).

## Setup

| | |
| --- | --- |
| Model | `qwen3.8:27b`, 27.3B parameters, Q4_K_M (GGUF), Ollama digest `aaee06c39dcf` |
| Server | Ollama 0.40.5, ROCm 7.2, Radeon 8060S (32 GB of 64 GB unified memory), GMKtec EVO-X2 (Ryzen AI Max+ 395), Ubuntu 26.04.1; context 65,536, flash attention, one request at a time |
| Sampling | model defaults: temperature 1.0, top_k 20, top_p 0.95; seed = GSM8K index on every call |
| Calls | Ollama `/api/generate`, raw mode, the model's own chat format with thinking on. No Codex, no agent harness |
| Items | 144 GSM8K test problems with 3+ reference steps. An error is planted at the first step (early) and the second-to-last (late): the step's result moved by 10% to 50%, with the "follow" answer replayed exactly |
| Conditions | free run; control and planted continuations at each step; forced answers with no thinking, before each step, and after the full thinking |

## Results

### Accuracy by condition

| condition | right |
| --- | --- |
| free (think, then reply) | 135/144 (94%) |
| forced answer, no thinking | 33/144 (23%) |
| forced answer, thinking cut before the early step | 28/120 (23%) |
| forced answer, thinking cut before the late step | 67/117 (57%) |
| forced answer, after the full thinking | 135/144 (94%) |
| control continuation, early step | 115/120 (96%) |
| control continuation, late step | 114/117 (97%) |

### Planted errors (free answer right, step found in the thinking)

The step's result was found in the thinking in 120 (early) and 117 (late) of 144 problems. Elsewhere, the model's working differed from the reference solution.

| position | runs | followed the error (95% CI) | recovered | other |
| --- | --- | --- | --- | --- |
| early | 115 | 34 (30%, 21 to 38) | 79 | 2 |
| late | 115 | 47 (41%, 32 to 50) | 68 | 0 |
| both | 230 | 81 (35%) | 147 | 2 |

### Hypotheses (preregistered, Holm-adjusted together)

The unit is the item.

| # | comparison | items | items + / 0 / − | mean per item (95% CI) | p | Holm p |
| --- | --- | --- | --- | --- | --- | --- |
| H1 | wrong, planted − control | 129 | 68 / 60 / 1 | +37.2 pts (+30.2 to +44.2) | < 0.001 | < 0.001 |
| H2 | followed, late − early (two-sided) | 101 | 25 / 64 / 12 | +12.9 pts (+1.0 to +24.8) | 0.047 | 0.047 |
| H3 | right, full thinking − no thinking | 144 | 103 / 40 / 1 | +70.8 pts (+63.2 to +78.5) | < 0.001 | < 0.001 |

All three are supported.

### Reported without a test (preregistered)

- **Noticed:** of the 147 recovered runs, 126 had a correction in the continued thinking by the preregistered rule: the true value restated, or a word such as "wait" or "recalculate".
- **Mismatch:** in 23 planted runs (12 early, 11 late), the thinking's last number was the follow answer but the reply gave a different one. In 0 runs did the thinking end on the right answer with a different reply.

### Time, tokens and cost

| call | n | median s | total h | mean new tokens |
| --- | --- | --- | --- | --- |
| free | 144 | 9.1 | 0.46 | 329 |
| planted continuation | 237 | 7.9 | 0.63 | 280 |
| control continuation | 237 | 6.3 | 0.49 | 210 |
| forced answers | 525 | 0.7 | 0.12 | 4 |

- **Energy:** 145 Wh of APU package power over the 1.71-hour run, £0.036 at £0.25/kWh.
- **Hosted-price equivalent:** $0.24 at `gpt-5.6-luna` list prices. This is a lower bound, because Ollama counts only the prompt tokens it had to process. There is no hosted run to compare: hosted reasoning can't be read or edited (see [What changed](#what-changed-from-the-design)).

## Checks on the runs

- **All 144 problems ran every applicable condition.** No call errored. No free run or continuation hit the 8,000-token limit. Every free run closed its thinking.
- **Server and model were recorded at the start** ([results/main/server.txt](results/main/server.txt)): Ollama 0.40.5, `qwen3.8:27b` digest `aaee06c39dcf…`, Q4_K_M, context 65,536, flash attention, one request at a time. Every result file names `qwen3.8:27b`.
- **The prompt format was checked before the run.** The raw prompt is the same 114 tokens as Ollama's own chat call with thinking on.
- **Reproducible:** with fixed seeds, rerunning the dry-run items gave identical answers.
- **The text counts were checked by reading transcripts.**
  - All 23 mismatches were read: in each one, the thinking ends on the follow answer and the reply gives the right answer.
  - A sample of recovered runs was read: the correction is explicit in the thinking ("Wait, let me recalculate. … 16 + 32 + 64 + 128 = 240 … 240 / 4 = 60").
- **Item checks:** every follow answer is an exact replay of the reference steps with the planted value, and was hand-checked on the first item.

## Exploratory analysis, added after the results

Not part of the preregistered analysis. Counts come from simple searches of the recorded text, and the patterns from reading transcripts.

- **Where the recoveries happened.** The 147 recoveries split two ways:
  - **124:** the thinking restated the step's true value and carried on correctly;
  - **23:** the thinking ended on the wrong answer and only the reply fixed it.
- **Typical catch:** the model writes the next line using the planted number, then stops: "Hmm, that gives fewer chairs than sofas, which contradicts '2 fewer sofas than chairs'. Let me re-read." It's often a sanity check against the question, not re-doing the sum.
- **Typical follow:** the planted number is used as if it were its own, with no comment. On item 238, "Mary = Joan - 2 = 25 - 2 = 33" (33 planted) led straight to "Sum of ages = Jessa + Joan + Mary = 20 + 25 + 33 = 78".
- **Typical mismatch:** on item 467, the thinking "double-checks", restates "2 × 2 = 3" and concludes 960. The reply then starts again ("Pillow cases: twice as many as sheets = 2 × 2 = 4") and answers 1,200. Nothing in the reply says the thinking was wrong.
- **Doubt when following:** 7 of the 81 followed runs had a correction word in the thinking but still ended on the follow answer. Only 1 of the 81 replies did.

## What this means in practice: impact and risks

This section is interpretation, not measurement. It goes beyond what one model on school maths can show, and says so where it does.

**1. Bad data in the reasoning becomes a confident wrong answer, about a third of the time.**
- **What was measured:** a wrong intermediate number in the thinking reached the final answer in 35% of cases. Almost every time, the reply gave no hint of a problem.
- **Where this bites:** a planted number in the thinking is a stand-in for any wrong figure that gets into the model's working, such as:
  - a misread value from a document;
  - a wrong result from a tool or spreadsheet;
  - a number an attacker has slipped into a web page or file the model reads (prompt injection).
  The experiment didn't test those routes directly. But the mechanism is the same: the model builds on what's in its context.
- **What follows:** an assistant that reads your invoices, logs or search results can repeat someone else's error as its own conclusion, in the same confident tone as a right answer.

**2. "It checks its own work" is true about half the time.**
- **What was measured:** the model caught 54% of the slips. These were blatant ones: the wrong result sat right next to the sum that produced it, as in "4 × 20 = 55".
- **What follows:**
  - Subtler errors are likely caught less often. A wrong reading of the problem, or a plausible but wrong figure from a source, has no sum beside it to contradict.
  - Self-correction is a useful habit, not a safeguard. Late errors were caught less often than early ones, and late is where a contaminated figure would do most harm.

**3. The visible thinking isn't a reliable record of how the answer was reached.**
- **What was measured:** in 1 run in 10, the thinking concluded one answer and the reply gave another, without saying why.
- **What follows:** the "audit trail" view of visible reasoning has a hole.
  - **Who relies on that view:** reviewers who read the reasoning to decide whether to trust an answer; automated monitors that scan reasoning for problems; products that show a summary of the model's thinking as its explanation.
  - **This direction is benign:** here the reply was right and the thinking wrong.
  - **The risk is general:** if the thinking and the answer can come apart in one direction without comment, a monitor reading only the thinking is checking something other than what the model finally said. Anyone using reasoning for oversight in areas where explanations matter should check the final answer and its own working, not the thinking alone. That includes finance, health, legal work and safety monitoring.

**4. What a reader can do:**
- Check key numbers against the source yourself, especially ones the model got from documents or tools.
- Treat a confident tone as uninformative. Followed errors were stated just as firmly as right answers, which matches the judge's confidence in the [diff-judge experiment](../2026-10-diff-judge/REPORT.md).
- Don't treat a model's reasoning, or a summary of it, as proof of how it got its answer. Ask it to show the working in the answer, and check that.
- Where an answer matters, have something other than the model's own judgement check it: a calculation, a test, or a second source.

**What it doesn't show:**
- That hosted reasoning models behave the same way. Their reasoning can't be edited, so this experiment can't be run on them.
- That the model's natural mistakes behave like planted ones.

## How far the result goes

- **One model:** `qwen3.8:27b` at 4-bit quantisation, at its default sampling. Other models, larger ones or ones trained differently, may follow or catch errors at different rates.
- **School maths only:** problems with exact answers. The errors were arithmetic slips placed beside their own sums, which makes them easier to spot than most real errors.
- **Planted, not natural, errors.** The model didn't make these mistakes itself. The text was edited, and the model may treat an out-of-place number differently from its own slip.
- **One run per condition,** with fixed seeds.
- **The analysis set is filtered:** the 81–83% of problems whose working matched the reference step, and only problems the model first got right.
- **The text-based counts are approximate** ("noticed", "mismatch"). Reading confirmed all 23 mismatches and a sample of the rest, not every run.

## What changed from the design

- **No hosted arm, and no Codex.** Recorded before the run in the [README's amendment log](README.md#amendment-log), with the user's words.
- **Nothing else changed.** The design, hypotheses and analysis script ran as committed. The breakdown of recoveries, the reading of transcripts, and the impact and risks section were added after the results.

## Reproducing

```
python3 -I scripts/make_items.py <gsm8k test.jsonl> items/items.json
scripts/run_all.sh <out dir>
scripts/export.sh <out dir> main
python3 -I scripts/analyse.py results/main > results/analysis.md
```
