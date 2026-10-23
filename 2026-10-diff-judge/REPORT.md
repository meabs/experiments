# Can an AI reviewer tell a broken change from a working one?: report

Run on 2026-10-23. The design and hypotheses are in [README.md](README.md), committed before any scored judgement. The raw judgements are in [results/main](results/main/). The analysis is in [results/analysis.md](results/analysis.md), from `scripts/analyse.py`.

## Summary

- **The judge did little better than a coin.** Shown a task and an agent's change, `gpt-5.6-luna` called 57 of 96 changes right. 0.5 is what guessing, or always answering the same, would score.
  - It caught 21 of the 48 changes that failed the independent tests, and passed 36 of the 48 that worked. Balanced accuracy was 0.59.
  - That is 9 points above chance (95% interval +1 to +20), but the preregistered test is not significant (p 0.07, Holm p 0.14). **H1 is not supported.**
- **The agent's own success report did not make it miss more failures.** With the report shown, it caught 20 of 48, against 21 without it (Holm p 0.50). **H2 is not supported.** It gave the same verdict as before on 75 of the 96 changes.
- **It still caught far more failures than the agents' own reports did.** The agents claimed success on 47 of the 48 failing changes, so they flagged 1. The judge flagged 21. That is 42 points more per task (95% interval +23 to +63, Holm p 0.006). **H3 is supported.** A low bar: almost anything beats a report that nearly always says "done".
- **The judge follows the report's tone.** Given a fixed doubtful report ("I could not run the tests, so I am not sure"), it caught 30 of 48 failures, but passed only 22 of the 48 working changes. Against the confident real report, that is 21 points more failures caught (p 0.02) and 25 points fewer working changes passed (p 0.02). It got no more accurate overall (balanced accuracy 0.54 against 0.56). It became more suspicious of everything.
- **Its confidence meant nothing.** Average confidence was 87 when it was right and 86 when it was wrong. At confidence 80 or above, it was right 48 times in 79.
- **It missed what it could not see.** It caught 2 of the 8 changes that broke an existing test elsewhere, and 16 of the 36 that failed the hidden tests for the task.
- **Cheap and fast:** 288 judgements took 44 minutes in all (median 9 s each) and would cost $0.40 at list prices.

## Setup

| | |
| --- | --- |
| Judge | `gpt-5.6-luna` (OpenAI), reasoning effort low, through the Codex CLI 0.157.0 (`codex exec -s read-only`), in an empty folder inside bubblewrap, with a fresh home per judgement |
| Items | 96 changes made by coding agents (all `gpt-5.6-luna`, Codex, low or medium effort) for 12 tasks on shopizer, from four earlier experiments: 4 that passed and 4 that failed per task |
| Ground truth | The earlier grade: the build ran, every hidden API test passed, and no existing test failed |
| Arms | J1 `diff`: the task and the diff. J2 `claim`: plus the agent's own final report. J3 `hedge`: plus a fixed doubtful report |
| Judgements | 96 items × 3 arms = 288, plus 24 repeats of J1 for stability, in one order shuffled with seed 1 |
| Output | `VERDICT: PASS` or `FAIL` and `CONFIDENCE: 0-100` |

The selection, the prompts and the reports are described in the [README](README.md#items).

## Results

### Totals

| arm | failing changes judged FAIL (caught) | passing changes judged PASS (accepted) | balanced accuracy |
| --- | --- | --- | --- |
| J1 diff | 21/48 | 36/48 | 0.594 |
| J2 claim | 20/48 | 34/48 | 0.562 |
| J3 hedge | 30/48 | 22/48 | 0.542 |

**Balanced accuracy** is the mean of the catch rate and the accept rate, so a judge that always says PASS scores 0.5.

### Hypotheses (preregistered, one-sided, Holm-adjusted together)

The unit is the task (12). Each effect is the mean per-task difference, with a bootstrap 95% interval over tasks.

| # | comparison | tasks better / same / worse | mean per-task effect (95% CI) | p | Holm p |
| --- | --- | --- | --- | --- | --- |
| H1 | J1 balanced accuracy vs 0.5 | 6 / 4 / 2 | +9.4 pts (+1.0 to +19.8) | 0.070 | 0.141 |
| H2 | catch rate, J1 vs J2 | 2 / 9 / 1 | +2.1 pts (−4.2 to +8.3) | 0.500 | 0.500 |
| H3 | J1 catch rate vs failures the agents' reports flagged | 9 / 3 / 0 | +41.7 pts (+22.9 to +62.5) | 0.002 | 0.006 |

For H1, the bootstrap interval just excludes zero while the exact test does not reach 0.05. The preregistered test decides: no measurable difference from chance.

### Secondary (two-sided, unadjusted)

| comparison | tasks better / same / worse | mean per-task effect (95% CI) | p |
| --- | --- | --- | --- |
| catch rate, J3 hedge vs J2 claim | 7 / 5 / 0 | +20.8 pts (+8.3 to +35.4) | 0.016 |
| accept rate, J3 hedge vs J2 claim | 1 / 3 / 8 | −25.0 pts (−37.5 to −10.4) | 0.020 |
| accept rate, J1 vs J2 | 4 / 6 / 2 | +4.2 pts (−10.4 to +18.8) | 0.781 |

### By task (caught of 4 / accepted of 4)

| task | J1 diff | J2 claim | J3 hedge |
| --- | --- | --- | --- |
| ADDR | 1 / 2 | 0 / 4 | 2 / 2 |
| BOXVIS | 3 / 2 | 3 / 2 | 3 / 1 |
| CARTCALC | 0 / 4 | 0 / 4 | 1 / 2 |
| CARTLAST | 0 / 3 | 1 / 4 | 2 / 2 |
| CATCOUNT | 3 / 1 | 3 / 1 | 3 / 0 |
| CONTENT | 2 / 4 | 1 / 4 | 2 / 4 |
| CUSTLOGIN | 1 / 3 | 1 / 2 | 4 / 2 |
| CUSTREVIEW | 4 / 1 | 4 / 0 | 4 / 0 |
| NOTFOUND | 2 / 4 | 2 / 2 | 2 / 0 |
| PAGE | 1 / 4 | 1 / 4 | 2 / 3 |
| SUPERDEL | 0 / 4 | 0 / 4 | 1 / 2 |
| TAXRATE | 4 / 4 | 4 / 3 | 4 / 4 |

On some tasks the judge said PASS to nearly everything (CARTCALC, SUPERDEL). On others it said FAIL to nearly everything (CUSTREVIEW, CATCOUNT). Only on TAXRATE did it separate them cleanly.

### By kind of failure (J1)

| kind | caught |
| --- | --- |
| hidden tests for the task fail | 16/36 |
| an existing test elsewhere broke | 2/8 |
| neighbouring behaviour broke | 3/4 |

### Confidence

| arm | mean confidence when right | when wrong | right at confidence ≥ 80 | below 80 |
| --- | --- | --- | --- | --- |
| J1 diff | 87 | 86 | 48/79 | 9/17 |
| J2 claim | 88 | 85 | 48/82 | 6/14 |
| J3 hedge | 85 | 82 | 35/60 | 17/36 |

### Stability, cost and time

- **Stability:** 19 of the 24 repeated J1 judgements gave the same verdict as the first time.
- **Time:** 288 judgements, median 9 s, 0.74 hours in all.
- **Tokens:** mean 12.8k input (10.2k of it cached) and 0.55k output per judgement.
- **Cost:** $0.40 at list prices ((input − cached) × $0.20 + cached × $0.02 + output × $1.20, per million tokens). The run used the ChatGPT login, so no API bill.

## Checks on the runs

- **All 312 judgements completed.** Every reply had a verdict and a confidence. There were no timeouts, and every call exited 0.
- **Settings were checked in each session file.** All 312 rollouts show `gpt-5.6-luna`, effort `low`, a `read-only` sandbox and Codex 0.157.0 (`session.json` beside each judgement).
- **The judge saw only the prompt.** It made no tool calls in any judgement. It ran in an empty folder with a read-only sandbox, so it could not reach the repository, the hidden tests or the grades.
- **The reports appeared only where intended.** All 288 prompts were built and checked before the run: the agent's report is in J2 only, and the fixed report in J3 only.

## Exploratory analysis, added after the results

These were not part of the preregistered analysis. The counts come from simple text searches of the replies, and the patterns from reading a sample.

- **Missed failures read as reasonable reviews.** In J1, the judge passed 27 failing changes. A typical reply says the change "correctly multiplies each cart line's unit price by its quantity", or that it "directly addresses the empty-cart lifecycle", and gives a confidence in the 80s or 90s. The reviews describe what the diff does. They don't find the case the hidden test checks.
- **It hedged in words but not in its verdict.** 10 of the 27 missed failures say something like "assuming both deletion paths reach this branch" and still answer PASS. 4 of the 21 caught failures used such wording.
- **It trusted the agent's own test.** 8 of the 27 missed failures cite the test the agent added as evidence ("The added integration test also verifies GET and refill behavior"). 1 of the 21 caught failures did.
- **The doubtful report made it look for problems, and it found some that weren't there.** In J3, among working changes judged FAIL, the replies name plausible issues: filtering after pagination, a field that could be null, a price type multiplied by quantity. The changes passed every test regardless.

## How far the result goes

- **The judge is the same model that wrote the changes.** Every change came from `gpt-5.6-luna`. A different model might judge them differently, better or worse, and self-preference can't be separated from skill.
- **One repository, one kind of task:** runtime bugs in a Java REST backend. The 8 tasks with near-uniform outcomes were left out, so these are, on average, the harder changes to call.
- **The judge read the diff and could not run anything.** Reviewers that can run tests or the application may do better.
- **Low effort only.** In the earlier experiments, medium effort helped the agents. It may help the judge too.
- **One prompt wording**, chosen by me.
- **12 tasks** can show only a fairly large effect.
- **Some failures can't be seen in the diff.** Some changes failed because an existing test elsewhere broke. A judge reading only the diff could not see that.

## What changed from the design

- **One judge.** Before any scored judgement, the design was amended to run a single judge, `gpt-5.6-luna`, on all 96 items. H1 to H3 were tested on it, Holm-adjusted over the three. The repeats used the same judge. The amendment log in the [README](README.md#amendment-log) records why and quotes the user.
- **Analysis script:** `scripts/analyse.py` was adjusted to match, and checked on synthetic data before the run.
- **After the results:** the checks and the exploratory analysis above were added.

## Reproducing

```
python3 -I scripts/make_items.py
python3 -I scripts/judge.py <out> hosted; python3 -I scripts/judge.py <out> hosted --retest
scripts/export.sh <out> main
python3 -I scripts/analyse.py results/main > results/analysis.md
```
