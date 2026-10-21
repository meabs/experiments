# Trial report: skills-impact

Baseline arm: **none**. Relative cost is each run's tokens divided by the baseline's mean for the same question; 1.00 means equal, lower is cheaper.

## codex

| arm | runs | correct | tokens per run (95% CI) | relative cost (95% CI) | verdict | turns | used tool | seconds | claimed vs verified |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| none | 18 | - (verified 16/18) | 2172k (1575k to 2858k) | 1.00 | baseline | 26.6 | - | 148 | 2 overclaim, 16 agree |
| placebo | 18 | - (verified 14/18) | 2564k (1930k to 3249k) | 1.16 (0.96 to 1.39) | no clear difference | 30.9 | 18/18 | 161 | 3 overclaim, 1 underclaim, 14 agree |
| superpowers | 18 | - (verified 18/18) | 5865k (4570k to 7156k) | 2.62 (2.33 to 2.92) | dearer | 36.2 | 18/18 | 303 | 18 agree |
| pocock | 18 | - (verified 15/18) | 2973k (2367k to 3607k) | 1.41 (1.20 to 1.62) | dearer | 29.0 | 7/18 | 186 | 3 overclaim, 15 agree |

Run-to-run spread (coefficient of variation of relative cost) is 0.48. To detect a 20% difference with 80% power you would need about **92 runs per arm** (larger differences need fewer); this trial has 18.

## cursor

| arm | runs | correct | tokens per run (95% CI) | relative cost (95% CI) | verdict | turns | used tool | seconds | claimed vs verified |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| none | 18 | - (verified 18/18) | 519k (393k to 657k) | 1.00 | baseline | 40.2 | - | 133 | 13 underclaim, 5 agree |
| placebo | 18 | - (verified 18/18) | 490k (392k to 602k) | 0.96 (0.82 to 1.11) | no clear difference | 40.0 | 18/18 | 120 | 16 underclaim, 2 agree |
| superpowers | 18 | - (verified 18/18) | 975k (813k to 1157k) | 1.93 (1.72 to 2.14) | dearer | 58.1 | 18/18 | 180 | 18 agree |
| pocock | 18 | - (verified 16/18) | 663k (550k to 783k) | 1.33 (1.13 to 1.54) | dearer | 48.1 | 11/18 | 148 | 1 overclaim, 7 underclaim, 10 agree |
| pstack | 18 | - (verified 18/18) | 1183k (1000k to 1389k) | 2.38 (2.05 to 2.70) | dearer | 68.2 | 18/18 | 219 | 5 underclaim, 11 agree, 2 none |

Run-to-run spread (coefficient of variation of relative cost) is 0.45. To detect a 20% difference with 80% power you would need about **80 runs per arm** (larger differences need fewer); this trial has 18.

## Tokens by question (mean, thousands)

| question | codex/none | codex/placebo | codex/pocock | codex/superpowers | cursor/none | cursor/placebo | cursor/pocock | cursor/pstack | cursor/superpowers |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BUG | 1109k | 1181k | 1646k | 2478k | 407k | 272k | 697k | 1225k | 722k |
| CROSS | 2376k | 3030k | 3708k | 7064k | 354k | 456k | 412k | 762k | 792k |
| FEAT | 3032k | 3481k | 3566k | 8053k | 794k | 741k | 879k | 1561k | 1413k |

## What agents said was missing

Self-reported, so a lead to check and not a finding.

| note | runs | arms |
| --- | --- | --- |
| a cart API test or fixture that sets CART_MAX_LINE_QUANTITY and asserts the rejected request | 2 | pocock |
| an integration test or fixture that sets CART_MAX_LINE_QUANTITY and calls POST /api/v1/cart, PUT /api/v1/cart/{code}, and POST /api/v1/cart/{code}/multi | 2 | pocock, superpowers |
| A ProductPriceUtils test with a special amount plus start and end dates, and a product-create mapper test that asserts the end date is stored on productPriceSpecialEndDate. | 1 | placebo |
| A REST integration fixture specifically covering configured limits and persisted-cart equality after rejection. | 1 | pocock |
| A dedicated REST test covering valid website persistence and invalid URL rejection. | 1 | none |
| A dedicated cart-limit test fixture. | 1 | none |
| A dedicated product manufacturer website integration fixture. | 1 | superpowers |
| A dedicated product-response fixture/test. | 1 | pocock |
| A dedicated website API integration test. | 1 | pocock |
| A documented REST fixture for updating merchant configuration | 1 | pocock |

## What agents said they could not verify

Self-reported, so a lead to check and not a finding.

| note | runs | arms |
| --- | --- | --- |
| HTTP 400 on an invalid website | 8 | none, placebo, pocock |
| HTTP 400 on a bad website | 3 | placebo, pstack |
| persistence of a valid website | 3 | placebo, pocock, pstack |
| that a configuration change applies without a restart | 3 | placebo, pocock |
| JSON website on manufacturer detail, list, and product responses | 2 | none, superpowers |
| live admin and storefront HTTP APIs | 2 | pocock, pstack |
| A dedicated live HTTP test for the new limit was not run. | 1 | pocock |
| Configured-limit and live-update scenarios were not covered by existing integration tests | 1 | none |
| Custom configured-limit integration behavior was not directly exercised | 1 | placebo |
| Dedicated HTTP test changing the setting through a live merchant-configuration endpoint | 1 | pocock |

Token totals are not comparable between agents (see adapters.py). Treat a verdict as evidence only when the interval excludes 1.00, and as provisional below 8 runs per arm.

