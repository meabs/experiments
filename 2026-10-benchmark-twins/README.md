# Do benchmark scores show real ability? (twins of GSM8K and HumanEval items)

**Final design, committed 2026-10-23 before any measured answer.** Later changes go in the amendment log at the bottom.

## Why

Models are sold on benchmark scores, and GSM8K (school maths word problems) and HumanEval (short Python functions) are two of the best known. Both have been public for years, so their questions and answers are very likely in the models' training data. A high score could mean the model reasons, or that it has seen the item.

One way to tell the difference: change the parts of a question that do not matter to its difficulty, such as the numbers or the names, work out the new answer mechanically, and ask again. A model that reasons should score about the same. A model that remembers should score worse on the twin.

## Question

Does a model answer an unchanged benchmark item more often than a twin of it, with new numbers, new names or a renamed function, of the same difficulty and with an answer computed without any model? Does the drop differ between a local open-weight model and a hosted one?

## Models and harness

| | local | hosted |
| --- | --- | --- |
| Model | `qwen3.8:27b`, 27.3B parameters, Q4_K_M (GGUF), Ollama digest `aaee06c39dcf` | `gpt-5.6-luna` (OpenAI), through the user's ChatGPT login |
| Server | Ollama 0.40.5, ROCm 7.2, Radeon 8060S (32 GB of 64 GB unified memory), context 65,536 | OpenAI |
| Sampling | Ollama defaults: temperature 1.0, top_k 20, top_p 0.95 | provider default |
| Reasoning effort | low | low |
| Harness | Codex CLI 0.157.0, `codex exec -s read-only --json`, in an empty folder inside bubblewrap, with a fresh home per answer. The local model uses the Codex set-up of [2026-10-test-skill-local](../2026-10-test-skill-local/) | the same, with luna's built-in settings |

- Each answer is one call with one prompt. The model cannot open files or run code: the sandbox is read-only and the folder is empty.
- **Reasoning effort** tells the model how long to think before answering. **Tokens** are the units a model reads and writes, about four characters each.

## Items

Built with no language model, from the public test sets ([`items/SOURCE.md`](items/SOURCE.md) gives the files and their hashes).

### GSM8K: [`scripts/make_gsm8k_twins.py`](scripts/make_gsm8k_twins.py), [`items/gsm8k-twins.json`](items/gsm8k-twins.json)

- Each GSM8K reference solution marks its arithmetic as calculator steps (`<<48/2=24>>`). The script replays those steps with exact fractions.
- It keeps only items where every number in a step is explained: a number written in the question, a number word, an earlier result, or a unit constant. The replay must reproduce every original result. Items where a number could be two things are skipped. So are items with arithmetic outside the marked steps.
- **184 of the 1,319 items** qualify. The skip reasons are in [`items/make_gsm8k_twins.out`](items/make_gsm8k_twins.out).
- **Variants:**
  - `orig`: the original question.
  - `numbers`: every number in the question changed, and the answer recomputed by the same steps. Each new number keeps its digit count, stays within 0.5x to 1.5x of the old one, keeps the same rounding (multiple of 10 or 5), and keeps the same order among the question's numbers. Every step keeps its sign and stays a whole number where it was one. The answer changes but keeps its digit count. All 184 items.
  - `names`: first names swapped for others of the same list (female or male), so pronouns still agree. 64 items, those with a name on the lists.
  - `both`: names and numbers together. The same 64 items.
- **Checks:** 30 items were checked by hand against the reference logic, and all 30 were consistent. Where GSM8K's own reference answer is wrong, the error is replayed into the twin, so both versions are graded by the same logic.

### HumanEval: [`scripts/make_humaneval_twins.py`](scripts/make_humaneval_twins.py), [`items/humaneval-twins-sample.json`](items/humaneval-twins-sample.json)

- **Variants:**
  - `orig`: the original prompt (signature and docstring).
  - `renamed`: the function renamed to `solution` everywhere in the prompt, its docstring examples included, and in the tests where they name it. Nothing else changes.
- 162 of the 164 items qualify. Two already use the name `solution`.
- For every item, the reference solution passes the original tests, and the reference solution renamed the same way passes the renamed tests.
- **Sample:** 80 of the 162, drawn with `random.Random(1).sample`, to fit the time budget.

### Dry-run items (never scored)

4 GSM8K items not among the 184 ([`items/dryrun.json`](items/dryrun.json)) and the 2 HumanEval items left out ([`items/humaneval-dryrun.json`](items/humaneval-dryrun.json)), used to try the prompts, the parsing and the timing.

## Prompts and grading

- **GSM8K** ([`arms/gsm8k-prompt.md`](arms/gsm8k-prompt.md)): the question, then "end your reply with one line of the form `ANSWER: <the final number only>`". Graded by exact numeric match of the last `ANSWER:` line, ignoring `$` and thousands separators.
- **HumanEval** ([`arms/humaneval-prompt.md`](arms/humaneval-prompt.md)): the prompt in a code block, then "Reply with the complete function... in one python code block". Grading ([`scripts/grade_code.py`](scripts/grade_code.py)):
  - The last code block of the reply is appended to the prompt and run with the item's tests.
  - It runs inside bubblewrap, with a read-only system, no network, no home folder and a 20-second limit.
  - Pass means every test passed.
- A reply with no answer, or a timeout, counts as wrong, and is reported.

## Size and time

- **Answers per model:** GSM8K 184 + 184 + 64 + 64 = 496; HumanEval 80 × 2 = 160. **656 in all.**
- **Order:** every (item, variant) pair, shuffled once with seed 1 per benchmark, the same order for both models ([`scripts/run.py`](scripts/run.py)). GSM8K runs first, then HumanEval.
- **Time limit:** 10 minutes per answer.
- **Measured on the dry-run items:**
  - Local: GSM8K 10–34 s, HumanEval 18–108 s. Projected about 2 hours for GSM8K and 1.5 hours for HumanEval, inside the budget of about 4 hours.
  - Hosted: 6–10 s per answer. It runs alongside the local model, on the CPU and network only.
- **Energy:** APU package power is logged once a second during the local run, at 0.25 £/kWh.
- **Hosted cost:** it runs through the ChatGPT login, so it counts against that plan. Shown at TSK's list prices ((input − cached) × $0.20 + cached × $0.02 + output × $1.20, per million tokens).

## Hypotheses and analysis (fixed before the runs)

The unit is the item. For each item and model, each variant is right or wrong, and the per-item effect is right on the original minus right on the twin (−1, 0 or +1).

- **Tests:** an exact sign-flip permutation test over items, computed by convolution ([`scripts/signflip_dp.py`](scripts/signflip_dp.py)). It is the same test as test-skill's `signflip_p`, checked against it on 600 random cases at every run.
- **Effects:** the mean per-item difference, with a bootstrap 95% interval over items (10,000 resamples, seed 1, test-skill's `boot`).
- **Holm adjustment:** `2026-10-skills-impact/scripts/stats.py`.

| # | Hypothesis | Per-item quantity | Test |
| --- | --- | --- | --- |
| H1 | The local model does worse on GSM8K numbers twins than on the originals | right(orig) − right(numbers), 184 items | one-sided |
| H2 | The local model does worse on GSM8K names twins than on the originals | right(orig) − right(names), 64 items | one-sided |
| H3 | The local model does worse on HumanEval renamed twins than on the originals | right(orig) − right(renamed), 80 items | one-sided |
| H4 | The local and hosted models differ in their GSM8K numbers-twin drop | local drop − hosted drop, 184 items | two-sided |

- H1 to H4 are Holm-adjusted together at α = 0.05.
- A non-significant result is reported as "no measurable difference".
- **A drop is a sign of memorisation, not proof.** A twin could be a little harder in a way the generator does not see. H4 helps here, because both models see the same twins.

**Secondary** (two-sided, unadjusted):

- H1 to H3 for the hosted model.
- `both` against `orig`, for both models.
- The numbers-twin drop by the number of calculator steps (2, 3, 4 or more).
- Replies without an answer, timeouts and tool calls.
- Time (median and total), tokens and cost for both models; energy for the local one.

**Exploratory, labelled so:** reading the replies to originals that were right and twins that were wrong, looking for signs of a remembered answer (for example, the original's answer given for the twin).

## Procedure

1. **Build the items. Done.**
2. **Dry run. Done**, on the dry-run items with both models: all 12 answers parsed and graded right.
3. **Run:** local and hosted at the same time ([`scripts/run_all.sh`](scripts/run_all.sh)), with power logged during the local run.
4. **Export** ([`scripts/export.sh`](scripts/export.sh)) and **analyse** ([`scripts/analyse.py`](scripts/analyse.py), checked on synthetic data before any measured answer).

## Known limits

- **Only a subset of GSM8K.** The 184 items are the ones whose arithmetic can be replayed mechanically: 1 to 7 calculator steps, most of them 2 or 3. They may be easier than the rest.
- **The brief also suggested reordering clauses.** That is not done, because it can't be made safe automatically.
- **Renaming a HumanEval function** to `solution` removes the hint in its name. A drop could come from that loss rather than from memory.
- **One run per item and variant,** at temperature 1.0 locally, so some differences are noise. The paired test accounts for this.
- **Low effort only,** for both models.
- **Benchmark items may sit in the training data of both models.** No data can say which items each model saw.

## Reproducing

```
python3 -I scripts/make_gsm8k_twins.py <gsm8k test.jsonl> items/gsm8k-twins.json
python3 -I scripts/make_humaneval_twins.py <HumanEval.jsonl.gz> items/humaneval-twins.json
scripts/run_all.sh <out dir>
scripts/export.sh <out dir> main
python3 -I scripts/analyse.py results/main > results/analysis.md
```

Machine set-up: [2026-10-test-skill-local/setup](../2026-10-test-skill-local/setup/).

## Amendment log

- 2026-10-23: design written at the user's request ("After the judge I want to do Benchmark scores show real ability" (memorised or reasoned?)), with the hosted comparison the brief offered "optionally ... with your approval", before any measured answer. The user approved the design and the hosted run: "Push, local + hosted".
