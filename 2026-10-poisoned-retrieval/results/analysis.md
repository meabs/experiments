# Poisoned retrieval: analysis

Questions with every answer recorded: 120. Models: qwen3.8_27b, qwen3_8b.

Retrieval: the answer paragraph was in bge-m3's natural top 5 for 59/120 (49%) of questions.

## Outcomes

| model | condition | right | follow | both | notfound | other | none |
| --- | --- | --- | --- | --- | --- | --- | --- |
| qwen3.8_27b | closed | 15 | 0 | 0 | 50 | 55 | 0 |
| qwen3.8_27b | clean | 113 | 0 | 0 | 3 | 4 | 0 |
| qwen3.8_27b | poisoned | 5 | 102 | 4 | 5 | 4 | 0 |
| qwen3.8_27b | miss | 5 | 1 | 0 | 107 | 7 | 0 |
| qwen3_8b | closed | 12 | 1 | 0 | 39 | 68 | 0 |
| qwen3_8b | clean | 104 | 0 | 0 | 11 | 5 | 0 |
| qwen3_8b | poisoned | 3 | 98 | 0 | 14 | 5 | 0 |
| qwen3_8b | miss | 2 | 1 | 0 | 112 | 5 | 0 |

## Hypotheses (preregistered, Holm-adjusted together)

| # | comparison | questions + / 0 / − | mean (95% CI) | p | Holm p |
| --- | --- | --- | --- | --- | --- |
| H1 | qwen3.8_27b: right, clean − poisoned | 108 / 12 / 0 | +90.0 pts (+84.2 to +95.0) | 0.000 | 0.000 |
| H2 | follows the planted value, 8B − 27B (poisoned) | 6 / 104 / 10 | -3.3 pts (-10.0 to +3.3) | 0.454 (two-sided) | 0.909 |
| H3 | makes up an answer when retrieval misses, 8B − 27B | 2 / 114 / 4 | -1.7 pts (-5.8 to +2.5) | 0.688 (two-sided) | 0.909 |

## Poisoned answers by what the model knew (closed book)

| model | closed book | questions | poisoned: right | follow | notfound | other | NOTE line in poisoned | NOTE line in clean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| qwen3.8_27b | right | 15 | 2 | 13 | 0 | 0 | 2 | 1 |
| qwen3.8_27b | not right | 105 | 3 | 89 | 5 | 4 | 15 | 8 |
| qwen3_8b | right | 12 | 1 | 11 | 0 | 0 | 1 | 0 |
| qwen3_8b | not right | 108 | 2 | 87 | 14 | 5 | 9 | 4 |

## When retrieval misses

| model | NOT FOUND | right anyway | made-up answer | of which closed book was right |
| --- | --- | --- | --- | --- |
| qwen3.8_27b | 107 | 5 | 8 | 0 |
| qwen3_8b | 112 | 2 | 6 | 0 |

## Time and tokens

| model | condition | median s | total h | mean prompt tokens | mean new tokens | errors | hit token limit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| qwen3.8_27b | closed | 19.5 | 0.85 | 66 | 612 | 0 | 0 |
| qwen3.8_27b | clean | 10.1 | 0.42 | 766 | 300 | 0 | 0 |
| qwen3.8_27b | poisoned | 9.4 | 0.44 | 766 | 333 | 0 | 0 |
| qwen3.8_27b | miss | 14.6 | 0.57 | 786 | 422 | 0 | 0 |
| qwen3_8b | closed | 29.4 | 1.24 | 63 | 742 | 0 | 0 |
| qwen3_8b | clean | 19.3 | 0.80 | 763 | 457 | 0 | 0 |
| qwen3_8b | poisoned | 19.2 | 0.92 | 763 | 528 | 0 | 0 |
| qwen3_8b | miss | 21.1 | 0.86 | 783 | 498 | 0 | 0 |

Tokens: 570,885 prompt (processed, not reused from the previous call), 467,122 new. At gpt-5.6-luna list prices (that input uncached; a lower bound): $0.67.

Energy (APU package power over the whole run, 6.10 h): 518 Wh, £0.130 at £0.25/kWh.
