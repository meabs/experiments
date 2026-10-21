# Trial report: skills-tasks

Baseline arm: **none**. Relative cost is each run's tokens divided by the baseline's mean for the same question; 1.00 means equal, lower is cheaper.

## codex

| arm | runs | correct | tokens per run (95% CI) | relative cost (95% CI) | verdict | turns | used tool | seconds | claimed vs verified |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| none | 32 | - (verified 24/32) | 375k (340k to 411k) | 1.00 | baseline | 7.2 | - | 45 | 7 overclaim, 25 agree |
| placebo | 32 | - (verified 23/32) | 401k (356k to 448k) | 1.09 (0.98 to 1.20) | no clear difference | 8.5 | 32/32 | 48 | 9 overclaim, 23 agree |
| superpowers | 32 | - (verified 24/32) | 1092k (943k to 1254k) | 3.07 (2.57 to 3.61) | dearer | 12.0 | 32/32 | 104 | 7 overclaim, 25 agree |
| pocock | 32 | - (verified 27/32) | 537k (436k to 662k) | 1.57 (1.19 to 2.05) | dearer | 9.0 | 27/32 | 60 | 5 overclaim, 27 agree |

Run-to-run spread (coefficient of variation of relative cost) is 0.75. To detect a 20% difference with 80% power you would need about **220 runs per arm** (larger differences need fewer); this trial has 32.

## Tokens by question (mean, thousands)

| question | codex/none | codex/placebo | codex/pocock | codex/superpowers |
| --- | --- | --- | --- | --- |
| ADDR | 258k | 416k | 731k | 1292k |
| AMBIG | 362k | 307k | 419k | 1298k |
| AVAIL | 409k | 366k | 476k | 1342k |
| CARTCALC | 276k | 346k | 1609k | 755k |
| CATCOUNT | 515k | 549k | 470k | 1036k |
| CATDUP | 387k | 349k | 503k | 1416k |
| CONTENT | 260k | 288k | 328k | 888k |
| CUSTDUP | 503k | 423k | 494k | 1235k |
| HCUST | 459k | 575k | 314k | 963k |
| HREVIEW | 337k | 370k | 471k | 778k |
| MANCODE | 392k | 550k | 381k | 671k |
| MANINUSE | 321k | 260k | 244k | 896k |
| MANORDER | 304k | 454k | 475k | 1564k |
| NOTFOUND | 467k | 585k | 477k | 635k |
| PAGE | 412k | 248k | 659k | 848k |
| TAXRATE | 335k | 324k | 538k | 1850k |

## What agents said was missing

Self-reported, so a lead to check and not a finding.

| note | runs | arms |
| --- | --- | --- |
| A focused category duplicate-code integration test or fixture | 1 | placebo |
| Running storefront fixture/server for endpoint-level verification | 1 | pocock |

## What agents said they could not verify

Self-reported, so a lead to check and not a finding.

| note | runs | arms |
| --- | --- | --- |
| API integration behavior was not exercised | 1 | placebo |
| Live HTTP responses and integration tests | 1 | pocock |

Token totals are not comparable between agents (see adapters.py). Treat a verdict as evidence only when the interval excludes 1.00, and as provisional below 8 runs per arm.

