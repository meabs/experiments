# Do benchmark scores show real ability? (twins of GSM8K and HumanEval items): report

Run on 2026-10-23 and 24. The design and hypotheses are in [README.md](README.md), committed before any measured answer. The raw answers are in [results/main](results/main/). The analysis is in [results/analysis.md](results/analysis.md), from `scripts/analyse.py`. A post-hoc check is in [results/sensitivity.md](results/sensitivity.md).

## Summary

- **Neither model did measurably worse on the twins.** Changing the numbers, the names or the function name barely moved either model's score. None of H1 to H4 is supported.

  | | original | twin |
  | --- | --- | --- |
  | local, GSM8K, new numbers | 168/184 | 161/184 |
  | local, GSM8K, new names | 59/64 | 59/64 |
  | local, HumanEval, renamed function | 75/80 | 72/80 |
  | hosted, GSM8K, new numbers | 175/184 | 172/184 |
  | hosted, GSM8K, new names | 63/64 | 63/64 |
  | hosted, HumanEval, renamed function | 75/80 | 75/80 |

  - **Local, new numbers:** 3.8 points lower on the twins (95% interval −1.6 to +9.2, Holm p 0.46). That is no measurable difference.
  - **Local and hosted drops:** no measurable difference between them (H4, Holm p 1.0).
- **A wrong answer on a twin was never the original's answer.** Each model got 15 numbers twins wrong with an answer given. In none of the 30 was the answer the original question's answer, which is what a remembered answer would look like.
- **Most of the local model's misses were harness failures, not wrong answers.** In 39 of its 656 replies, the local model tried to run a command, which the sandbox refused. It then put its answer in its reasoning instead of its reply, so it counted as "no answer". Regraded from that reasoning, after the results, 36 of them are right. The conclusion doesn't change: the largest gap left is 6 items against 1 on the GSM8K numbers twins (p 0.06, unadjusted).
- **On these items, the local model matched the hosted one.** Regraded, it scored 177 of 184 on the original GSM8K items against luna's 175, and 78 of 80 on HumanEval against 75.
- **Cost:**
  - Local: 2.97 hours of answering and 235 Wh of package power, about £0.06 at £0.25/kWh. The same tokens at the hosted list prices would cost $0.39.
  - Hosted: 1.15 hours (it ran alongside the local model), $0.39 at list prices.

## Setup

| | local | hosted |
| --- | --- | --- |
| Model | `qwen3.8:27b`, 27.3B parameters, Q4_K_M (GGUF), Ollama digest `aaee06c39dcf` | `gpt-5.6-luna` (OpenAI) |
| Server | Ollama 0.40.5, ROCm 7.2, Radeon 8060S (32 GB of 64 GB unified memory, GMKtec EVO-X2, Ryzen AI Max+ 395), context 65,536 | OpenAI, through the ChatGPT login |
| Sampling | temperature 1.0, top_k 20, top_p 0.95 (Ollama defaults) | provider default |
| Effort | low | low |
| Harness | Codex CLI 0.157.0, `codex exec -s read-only`, in an empty folder inside bubblewrap, a fresh home per answer | the same |

| | |
| --- | --- |
| GSM8K | 184 test items whose reference arithmetic could be replayed mechanically. Every item has a numbers twin; 64 also have a names twin and a twin with both. Answers recomputed exactly, with no model |
| HumanEval | 80 of 162 items, sampled with seed 1. Each has a twin with the function renamed to `solution` |
| Answers | 656 per model: GSM8K 496, HumanEval 160. All completed |
| Grading | GSM8K: exact numeric match of the last `ANSWER:` line. HumanEval: the item's tests, run in a sandbox with no network |

How the twins are built is described in the [README](README.md#items).

## Results

### Hypotheses (preregistered, Holm-adjusted together)

The unit is the item. For each item, the effect is right on the original minus right on the twin.

| # | comparison | items right only on original / same / right only on twin | mean effect (95% CI) | p | Holm p |
| --- | --- | --- | --- | --- | --- |
| H1 | local, GSM8K, original vs numbers twin | 16 / 159 / 9 | +3.8 pts (−1.6 to +9.2) | 0.115 | 0.459 |
| H2 | local, GSM8K, original vs names twin | 4 / 56 / 4 | +0.0 pts (−9.4 to +9.4) | 0.637 | 1.000 |
| H3 | local, HumanEval, original vs renamed twin | 7 / 69 / 4 | +3.8 pts (−3.8 to +12.5) | 0.274 | 0.823 |
| H4 | numbers-twin drop, local vs hosted (two-sided) | 14 / 160 / 10 | +2.2 pts (−3.3 to +7.6) | 0.541 | 1.000 |

None is supported: no measurable difference.

### Secondary (two-sided, unadjusted)

| comparison | right only on original / same / right only on twin | mean effect (95% CI) | p |
| --- | --- | --- | --- |
| hosted, GSM8K, numbers twin | 6 / 175 / 3 | +1.6 pts (−1.6 to +4.9) | 0.508 |
| hosted, GSM8K, names twin | 0 / 63 / 1 | −1.6 pts (−4.7 to 0.0) | 1.000 |
| hosted, HumanEval, renamed twin | 2 / 76 / 2 | 0.0 pts (−5.0 to +5.0) | 1.000 |
| local, GSM8K, both twin | 5 / 56 / 3 | +3.1 pts (−6.2 to +12.5) | 0.727 |
| hosted, GSM8K, both twin | 3 / 60 / 1 | +3.1 pts (−3.1 to +9.4) | 0.625 |

### Accuracy by variant

| model | benchmark | variant | right | no answer | timeouts |
| --- | --- | --- | --- | --- | --- |
| local | GSM8K | original | 168/184 | 9 | 0 |
| local | GSM8K | numbers | 161/184 | 11 | 0 |
| local | GSM8K | names | 59/64 | 4 | 0 |
| local | GSM8K | both | 57/64 | 4 | 0 |
| local | HumanEval | original | 75/80 | 3 | 0 |
| local | HumanEval | renamed | 72/80 | 8 | 2 |
| hosted | GSM8K | original | 175/184 | 0 | 0 |
| hosted | GSM8K | numbers | 172/184 | 1 | 0 |
| hosted | GSM8K | names | 63/64 | 0 | 0 |
| hosted | GSM8K | both | 60/64 | 0 | 0 |
| hosted | HumanEval | original | 75/80 | 0 | 0 |
| hosted | HumanEval | renamed | 75/80 | 0 | 0 |

### Numbers twin by number of steps (GSM8K)

| model | calculator steps | items | original right | twin right |
| --- | --- | --- | --- | --- |
| local | 1–2 | 85 | 82 | 75 |
| local | 3 | 63 | 54 | 56 |
| local | 4+ | 36 | 32 | 30 |
| hosted | 1–2 | 85 | 85 | 84 |
| hosted | 3 | 63 | 57 | 58 |
| hosted | 4+ | 36 | 33 | 30 |

No pattern: a drop from memory would be expected to grow, not vanish, with longer problems.

### Time, tokens and cost

| model | benchmark | answers | median s | total h | mean input | mean cached | mean output | $ at list prices |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| local | GSM8K | 496 | 8 | 1.39 | 7.2k | 6.9k | 0.21k | 0.22 (equivalent) |
| local | HumanEval | 160 | 17 | 1.58 | 7.3k | 6.9k | 0.69k | 0.17 (equivalent) |
| hosted | GSM8K | 496 | 6 | 0.87 | 11.7k | 10.2k | 0.08k | 0.29 |
| hosted | HumanEval | 160 | 6 | 0.28 | 11.7k | 10.2k | 0.11k | 0.10 |

- **Energy:** the local run used 235 Wh of APU package power over its answers, £0.06 at £0.25/kWh. The run took 2.97 hours from start to finish.
- **Token counts:** Ollama reports no separate reasoning tokens, so the local output counts include its reasoning. List prices are TSK's: (input − cached) × $0.20 + cached × $0.02 + output × $1.20, per million tokens.

## Checks on the runs

- **All 1,312 answers were recorded and graded.** The local model had 2 timeouts (10 minutes) and 39 replies with no answer, including those timeouts. The hosted model had 1 reply with no answer line, on item 1017's numbers twin (next point).
- **Settings were checked in each session file.** 656 rollouts show `qwen3.8:27b` through provider `ollama-local`, and 656 show `gpt-5.6-luna` through `openai`. All are effort `low`, sandbox `read-only`, Codex 0.157.0.
- **The models could not run code.** The local model tried 39 commands (to check arithmetic or test a function). Every one failed: Codex's own sandbox can't start inside the outer one. The hosted model tried none.
- **Every twin was checked before the run.** The GSM8K replay reproduces every original result. For HumanEval, the reference solution passes both the original and the renamed tests.
- **One GSM8K twin contradicts itself, found after the run.**
  - Item 1017's numbers twin reads "66 pictures... into 6 albums. 4 of the albums were selfies only and 3 of the albums were portraits", which is 7 albums out of 6. The generator keeps the order of the numbers, but not that the parts fit inside the whole.
  - The hosted model said the problem had no valid solution, and was graded wrong. The local model gave the mechanical answer, 77, and was graded right.
  - I then searched all 184 twins for any two numbers whose sum fitted under a third in the original but not in the twin. That flagged 8 items. Reading each, only 1017 is inconsistent.
  - Leaving it out would leave H1 unchanged and move H4 from +2.2 to +2.7 points.
- **The grader was checked before the run:** the code sandbox has no network and no home folder, and a wrong function fails.

## Exploratory analysis, added after the results

These were not part of the preregistered analysis.

- **Where the local model's "no answer" replies came from.** All 36 replies that called a tool ended without a final message (one of them after a timeout). The answer was there, but in the model's last reasoning item. The other 3 were 1 timeout and 2 empty replies. [`scripts/sensitivity.py`](scripts/sensitivity.py) regrades these replies from that reasoning, with the same parsing and grading ([results/sensitivity.md](results/sensitivity.md)):

  | comparison | right only on original / same / right only on twin | mean effect | p (unadjusted) |
  | --- | --- | --- | --- |
  | local, GSM8K, numbers twin | 6 / 177 / 1 | +2.7 pts | 0.063 |
  | local, GSM8K, names twin | 0 / 64 / 0 | 0.0 pts | 1.000 |
  | local, HumanEval, renamed twin | 1 / 78 / 1 | 0.0 pts | 0.750 |
  | numbers-twin drop, local vs hosted | 4 / 178 / 2 | +1.1 pts | 0.688 |

  Regraded, the local model scores 177/184 on original GSM8K items and 78/80 on HumanEval. The conclusion is the same: no measurable drop on the twins.
- **Wrong twin answers didn't repeat the original's answer.** 0 of 15 for each model.

## How far the result goes

- **No drop is not proof of no memorisation.** These twins keep the question's wording and logic. A model that learned how GSM8K problems work, rather than their answers, would pass them. They test whether answers are recalled, not whether the method generalises to new kinds of problem.
- **Easier subset.** The 184 GSM8K items are the ones whose arithmetic could be replayed mechanically, mostly 2 or 3 steps. Both models scored above 90% on them, which leaves little room for a drop.
- **The HumanEval twin is mild.** Renaming the function leaves the docstring and examples as they were.
- **One run per variant,** at temperature 1.0 locally. 80 to 184 items can show a drop of about 5 to 10 points, not 2.
- **Low effort only.**
- **Clause reordering,** suggested in the brief, was not done.
- **One flawed twin of 184** (item 1017, above), left in as graded, because the analysis was fixed before the run.
- **A harness interaction affected the local model only.** After a failed tool call, its answer went into its reasoning. That cut its preregistered scores on both originals and twins, and the regrading above shows it doesn't change the conclusion.

## What changed from the design

Nothing in the design, hypotheses or analysis. The sensitivity regrade and the other exploratory checks above were added after the results.

## Reproducing

```
python3 -I scripts/make_gsm8k_twins.py <gsm8k test.jsonl> items/gsm8k-twins.json
python3 -I scripts/make_humaneval_twins.py <HumanEval.jsonl.gz> items/humaneval-twins.json
scripts/run_all.sh <out dir>
scripts/export.sh <out dir> main
python3 -I scripts/analyse.py results/main > results/analysis.md
python3 -I scripts/sensitivity.py results/main items > results/sensitivity.md
```
