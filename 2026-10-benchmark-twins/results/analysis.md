# Benchmark twins: analysis

Answers: 1312; models: local, hosted.

## Accuracy

| model | benchmark | variant | right | no answer | timeouts |
| --- | --- | --- | --- | --- | --- |
| local | gsm8k | orig | 168/184 (91.3%) | 9 | 0 |
| local | gsm8k | numbers | 161/184 (87.5%) | 11 | 0 |
| local | gsm8k | names | 59/64 (92.2%) | 4 | 0 |
| local | gsm8k | both | 57/64 (89.1%) | 4 | 0 |
| local | humaneval | orig | 75/80 (93.8%) | 3 | 0 |
| local | humaneval | renamed | 72/80 (90.0%) | 8 | 2 |
| hosted | gsm8k | orig | 175/184 (95.1%) | 0 | 0 |
| hosted | gsm8k | numbers | 172/184 (93.5%) | 1 | 0 |
| hosted | gsm8k | names | 63/64 (98.4%) | 0 | 0 |
| hosted | gsm8k | both | 60/64 (93.8%) | 0 | 0 |
| hosted | humaneval | orig | 75/80 (93.8%) | 0 | 0 |
| hosted | humaneval | renamed | 75/80 (93.8%) | 0 | 0 |

## Hypotheses (preregistered)

Effect: accuracy on the original minus accuracy on the twin, over items with both. Positive means the twin is harder.

| # | comparison | items orig right only / same / twin right only | mean effect (95% CI) | p | Holm p |
| --- | --- | --- | --- | --- | --- |
| H1 | local, GSM8K: original vs numbers twin | 16 / 159 / 9 | +3.8 pts (-1.6 to +9.2) | 0.1148 | 0.4590 |
| H2 | local, GSM8K: original vs names twin | 4 / 56 / 4 | +0.0 pts (-9.4 to +9.4) | 0.6367 | 1.0000 |
| H3 | local, HumanEval: original vs renamed twin | 7 / 69 / 4 | +3.8 pts (-3.8 to +12.5) | 0.2744 | 0.8232 |
| H4 | GSM8K numbers-twin drop, local vs hosted | 14 / 160 / 10 | +2.2 pts (-3.3 to +7.6) | 0.5413 (two-sided) | 1.0000 |

## Secondary (two-sided, unadjusted)

| comparison | items orig right only / same / twin right only | mean effect (95% CI) | p |
| --- | --- | --- | --- |
| hosted, GSM8K: original vs numbers twin | 6 / 175 / 3 | +1.6 pts (-1.6 to +4.9) | 0.5078 |
| hosted, GSM8K: original vs names twin | 0 / 63 / 1 | -1.6 pts (-4.7 to +0.0) | 1.0000 |
| hosted, HumanEval: original vs renamed twin | 2 / 76 / 2 | +0.0 pts (-5.0 to +5.0) | 1.0000 |
| local, GSM8K: original vs both twin | 5 / 56 / 3 | +3.1 pts (-6.2 to +12.5) | 0.7266 |
| hosted, GSM8K: original vs both twin | 3 / 60 / 1 | +3.1 pts (-3.1 to +9.4) | 0.6250 |

## GSM8K numbers twin by number of steps

| model | steps | items | original right | twin right |
| --- | --- | --- | --- | --- |
| local | 2 | 85 | 82 | 75 |
| local | 3 | 63 | 54 | 56 |
| local | 4+ | 36 | 32 | 30 |
| hosted | 2 | 85 | 85 | 84 |
| hosted | 3 | 63 | 57 | 58 |
| hosted | 4+ | 36 | 33 | 30 |

## Time, tokens and cost

| model | benchmark | answers | median s | total h | mean input | mean cached | mean output | $ at list prices | tool calls attempted |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| local | gsm8k | 496 | 8 | 1.39 | 7.2k | 6.9k | 0.21k | 0.22 (equivalent) | 27 |
| local | humaneval | 160 | 17 | 1.58 | 7.3k | 6.9k | 0.69k | 0.17 (equivalent) | 12 |
| hosted | gsm8k | 496 | 6 | 0.87 | 11.7k | 10.2k | 0.08k | 0.29 | 0 |
| hosted | humaneval | 160 | 6 | 0.28 | 11.7k | 10.2k | 0.11k | 0.10 | 0 |

Local energy (APU package power over each answer): 235 Wh, £0.059 at £0.25/kWh.
