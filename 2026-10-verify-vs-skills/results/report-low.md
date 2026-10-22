# Trial report: verify-vs-skills

Baseline arm: **none**. Relative cost is each run's tokens divided by the baseline's mean for the same question; 1.00 means equal, lower is cheaper.

## codex

| arm | runs | correct | tokens per run (95% CI) | relative cost (95% CI) | verdict | turns | used tool | seconds | claimed vs verified |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| none | 60 | - (verified 36/60) | 410k (376k to 448k) | 1.00 | baseline | 7.8 | - | 51 | 24 overclaim, 1 underclaim, 35 agree |
| verify | 60 | - (verified 39/60) | 747k (675k to 827k) | 1.87 (1.70 to 2.08) | dearer | 10.4 | - | 85 | 20 overclaim, 5 underclaim, 35 agree |
| superpowers | 60 | - (verified 37/60) | 1287k (1112k to 1477k) | 3.13 (2.76 to 3.50) | dearer | 11.2 | 60/60 | 115 | 23 overclaim, 1 underclaim, 36 agree |

Run-to-run spread (coefficient of variation of relative cost) is 0.53. To detect a 20% difference with 80% power you would need about **112 runs per arm** (larger differences need fewer); this trial has 60.

## Tokens by question (mean, thousands)

| question | codex/none | codex/superpowers | codex/verify |
| --- | --- | --- | --- |
| ADDR | 407k | 1371k | 730k |
| AMBIG | 310k | 472k | 528k |
| AVAIL | 310k | 801k | 813k |
| BOXGET | 265k | 1152k | 464k |
| BOXVIS | 332k | 699k | 659k |
| CARTCALC | 353k | 1585k | 635k |
| CARTLAST | 554k | 1900k | 802k |
| CATCOUNT | 668k | 1199k | 661k |
| CATDUP | 492k | 1258k | 819k |
| CONTENT | 316k | 600k | 547k |
| CUSTDUP | 456k | 1237k | 734k |
| CUSTLOGIN | 379k | 1513k | 913k |
| CUSTREVIEW | 427k | 994k | 664k |
| NOTFOUND | 403k | 1116k | 789k |
| PAGE | 411k | 926k | 687k |
| REVEDIT | 342k | 1590k | 590k |
| REVIEW | 371k | 989k | 679k |
| SUPERDEL | 409k | 1721k | 1700k |
| TAXRATE | 557k | 3323k | 741k |
| USERERR | 444k | 1291k | 785k |

## What agents said was missing

Self-reported, so a lead to check and not a finding.

| note | runs | arms |
| --- | --- | --- |
| Configured integration-test database and fixtures | 1 | none |
| Configured storefront database and integration-test fixture | 1 | none |
| Content-box integration test fixture and test command | 1 | superpowers |
| Endpoint integration fixture or documented API test command | 1 | superpowers |
| Endpoint integration test or fixture | 1 | none |
| None | 1 | superpowers |

## What agents said they could not verify

Self-reported, so a lead to check and not a finding.

| note | runs | arms |
| --- | --- | --- |
| End-to-end duplicate registration behavior | 1 | none |
| Full Maven test suite | 1 | superpowers |
| Full project test suite | 1 | superpowers |
| HTTP endpoint responses directly | 1 | superpowers |
| Live API pagination behavior | 1 | none |
| Runtime API response and 404 behavior | 1 | none |
| Runtime HTTP behavior and automated tests | 1 | superpowers |

Token totals are not comparable between agents (see adapters.py). Treat a verdict as evidence only when the interval excludes 1.00, and as provisional below 8 runs per arm.

