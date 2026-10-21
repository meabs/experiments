# Caveman: analysis (Codex)

36 runs, statuses: ['ok'].

| task | arm | pass | QA mean F1 | median total tokens | median output tokens | median reply words | median articles per 100 words | median s | mean $ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| QA | none | 6/6 | 0.990 | 948k | 13.3k | 18 | 0.0 | 136 | 0.050 |
| QA | caveman | 6/6 | 0.999 | 914k | 12.2k | 18 | 0.0 | 116 | 0.044 |
| BUG | none | 5/6 | - | 1316k | 9.1k | 26 | 3.6 | 98 | 0.050 |
| BUG | caveman | 6/6 | - | 990k | 7.7k | 19 | 0.0 | 86 | 0.039 |
| FEAT | none | 6/6 | - | 3396k | 16.2k | 27 | 3.6 | 205 | 0.121 |
| FEAT | caveman | 6/6 | - | 2880k | 15.8k | 24 | 0.0 | 188 | 0.112 |

## Hypotheses (preregistered, Codex only)

| # | measure | caveman relative to none (95% CI) | rule | result |
| --- | --- | --- | --- | --- |
| C1 | output tokens | 0.87 (0.77 to 0.99) | interval entirely below 1.00 | supported |
| C2 | total tokens | 0.84 (0.69 to 1.03) | interval entirely below 0.80 | not supported |
| C3 | pass rate | 18/18 vs 17/18 | not lower by more than 3 of 18 | holds |

Per task (exploratory):

| task | output, relative (95% CI) | total, relative (95% CI) |
| --- | --- | --- |
| QA | 0.86 (0.72 to 1.03) | 0.84 (0.62 to 1.16) |
| BUG | 0.78 (0.63 to 0.96) | 0.75 (0.61 to 0.94) |
| FEAT | 0.97 (0.76 to 1.23) | 0.91 (0.58 to 1.37) |

Output is 0.9% of a `none` run's total tokens on average, so even removing all output would cut the total by about that much.

Total spend: $2.50 (list-price estimate).
