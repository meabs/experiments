# Trial report: caveman

Baseline arm: **none**. Relative cost is each run's tokens divided by the baseline's mean for the same question; 1.00 means equal, lower is cheaper.

## codex

| arm | runs | correct | tokens per run (95% CI) | relative cost (95% CI) | verdict | turns | used tool | seconds | claimed vs verified |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| none | 18 | - (verified 17/18) | 2034k (1432k to 2733k) | 1.00 | baseline | 27.1 | - | 150 | 1 overclaim, 4 underclaim, 13 agree |
| caveman | 18 | - (verified 18/18) | 1758k (1167k to 2447k) | 0.84 (0.72 to 0.97) | cheaper | 22.0 | 17/18 | 135 | 5 underclaim, 13 agree |

Run-to-run spread (coefficient of variation of relative cost) is 0.33. To detect a 20% difference with 80% power you would need about **44 runs per arm** (larger differences need fewer); this trial has 18.

## Tokens by question (mean, thousands)

| question | codex/caveman | codex/none |
| --- | --- | --- |
| BUG | 986k | 1310k |
| FEAT | 3394k | 3734k |
| QA | 893k | 1058k |

## What agents said was missing

Self-reported, so a lead to check and not a finding.

| note | runs | arms |
| --- | --- | --- |
| A dedicated cart-limit regression test fixture. | 1 | none |
| Dedicated dated-special regression test | 1 | none |
| Focused CART_MAX_LINE_QUANTITY test fixture | 1 | caveman |
| integration DB/REST fixture | 1 | caveman |
| live API/database fixture | 1 | caveman |

## What agents said they could not verify

Self-reported, so a lead to check and not a finding.

| note | runs | arms |
| --- | --- | --- |
| Dedicated limit/reload rollback test | 1 | caveman |
| Dedicated over-limit and live-configuration integration cases were not directly exercised. | 1 | none |
| No dedicated regression test for this exact merchant scenario | 1 | none |
| full REST/integration storefront flow | 1 | caveman |
| full live REST/storefront flow | 1 | caveman |

Token totals are not comparable between agents (see adapters.py). Treat a verdict as evidence only when the interval excludes 1.00, and as provisional below 8 runs per arm.

