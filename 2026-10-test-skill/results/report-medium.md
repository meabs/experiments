# Trial report: test-skill-medium

Baseline arm: **medium**. Relative cost is each run's tokens divided by the baseline's mean for the same question; 1.00 means equal, lower is cheaper.

## codex

| arm | runs | correct | tokens per run (95% CI) | relative cost (95% CI) | verdict | turns | used tool | seconds | claimed vs verified |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| medium | 60 | - (verified 49/60) | 877k (767k to 992k) | 1.00 | baseline | 10.5 | - | 95 | 10 overclaim, 1 underclaim, 49 agree |

## Tokens by question (mean, thousands)

| question | codex/medium |
| --- | --- |
| ADDR | 1094k |
| AMBIG | 644k |
| AVAIL | 617k |
| BOXGET | 514k |
| BOXVIS | 562k |
| CARTCALC | 773k |
| CARTLAST | 1260k |
| CATCOUNT | 1196k |
| CATDUP | 1003k |
| CONTENT | 481k |
| CUSTDUP | 1919k |
| CUSTLOGIN | 674k |
| CUSTREVIEW | 724k |
| NOTFOUND | 1136k |
| PAGE | 425k |
| REVEDIT | 1185k |
| REVIEW | 592k |
| SUPERDEL | 864k |
| TAXRATE | 816k |
| USERERR | 1055k |

## What agents said was missing

Self-reported, so a lead to check and not a finding.

| note | runs | arms |
| --- | --- | --- |
| Dedicated content list endpoint test | 1 | medium |
| No dedicated regression test for the exact empty-cart GET/add flow | 1 | medium |

## What agents said they could not verify

Self-reported, so a lead to check and not a finding.

| note | runs | arms |
| --- | --- | --- |
| Direct live API calls with persisted content fixtures | 1 | medium |

Token totals are not comparable between agents (see adapters.py). Treat a verdict as evidence only when the interval excludes 1.00, and as provisional below 8 runs per arm.

