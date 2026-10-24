# Planted errors: analysis

Items run: 144. Free answer right: 135/144 (94%). Thinking closed in the free run: 144.

## Accuracy by condition (all items)

| condition | right |
| --- | --- |
| free (think, then reply) | 135/144 (94%) |
| cut0 (no thinking, forced answer) | 33/144 (23%) |
| cut before the early step (forced answer), items located | 28/120 (23%) |
| control continuation at the early step, items located | 115/120 (96%) |
| cut before the late step (forced answer), items located | 67/117 (57%) |
| control continuation at the late step, items located | 114/117 (97%) |
| cutfull (whole thinking, forced answer) | 135/144 (94%) |

## Located plants

- early: located in 120/144 (83%) of items; 115 of the 135 with a right free answer.
- late: located in 117/144 (81%) of items; 115 of the 135 with a right free answer.

## Planted outcomes (analysis set: free answer right, plant located)

| position | n | follow (95% CI) | recover | other | recovered and noticed in thinking | thinking ended on follow answer, reply differs | thinking ended on right answer, reply differs |
| --- | --- | --- | --- | --- | --- | --- | --- |
| early | 115 | 34 = 30% (21 to 38) | 79 | 2 | 69 of 79 | 12 | 0 |
| late | 115 | 47 = 41% (32 to 50) | 68 | 0 | 57 of 68 | 11 | 0 |

## Hypotheses (preregistered, Holm-adjusted together)

| # | comparison | items | items + / 0 / − | mean (95% CI) | p | Holm p |
| --- | --- | --- | --- | --- | --- | --- |
| H1 | planted wrong − control wrong (per item, mean over its plants) | 129 | 68 / 60 / 1 | +37.2 pts (+30.2 to +44.2) | 0.000 | 0.000 |
| H2 | follow, late − early (items with both plants) | 101 | 25 / 64 / 12 | +12.9 pts (+1.0 to +24.8) | 0.047 (two-sided) | 0.047 |
| H3 | right, cutfull − cut0 (all items) | 144 | 103 / 40 / 1 | +70.8 pts (+63.2 to +78.5) | 0.000 | 0.000 |

## Time and tokens

| call | n | median s | total h | mean prompt tokens | mean new tokens | hit the token limit | errors |
| --- | --- | --- | --- | --- | --- | --- | --- |
| free | 144 | 9.1 | 0.46 | 79 | 329 | 0 | 0 |
| cut0 | 144 | 0.6 | 0.03 | 85 | 3 | 0 | 0 |
| cutfull | 144 | 0.8 | 0.04 | 285 | 4 | 0 | 0 |
| early control | 120 | 7.0 | 0.27 | 162 | 230 | 0 | 0 |
| early planted | 120 | 8.8 | 0.36 | 161 | 316 | 0 | 0 |
| early cut | 120 | 0.8 | 0.03 | 149 | 4 | 0 | 0 |
| late control | 117 | 5.7 | 0.22 | 198 | 189 | 0 | 0 |
| late planted | 117 | 6.5 | 0.27 | 198 | 243 | 0 | 0 |
| late cut | 117 | 0.8 | 0.03 | 185 | 4 | 0 | 0 |

All calls: 1143, 1.71 h of item time. Tokens: 189,257 prompt (processed, not reused from the previous call), 165,436 new. At gpt-5.6-luna list prices (that input uncached; a lower bound): $0.24.

Energy (APU package power over the whole run, 1.71 h): 145 Wh, £0.036 at £0.25/kWh.
