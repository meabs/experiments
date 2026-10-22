# Trial report: verify-vs-skills-medium

Baseline arm: **medium**. Relative cost is each run's tokens divided by the baseline's mean for the same question; 1.00 means equal, lower is cheaper.

## codex

| arm | runs | correct | tokens per run (95% CI) | relative cost (95% CI) | verdict | turns | used tool | seconds | claimed vs verified |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| medium | 60 | - (verified 49/60) | 888k (791k to 991k) | 1.00 | baseline | 10.6 | - | 97 | 11 overclaim, 1 underclaim, 48 agree |

## Tokens by question (mean, thousands)

| question | codex/medium |
| --- | --- |
| ADDR | 638k |
| AMBIG | 743k |
| AVAIL | 579k |
| BOXGET | 610k |
| BOXVIS | 587k |
| CARTCALC | 845k |
| CARTLAST | 1311k |
| CATCOUNT | 878k |
| CATDUP | 1078k |
| CONTENT | 397k |
| CUSTDUP | 1454k |
| CUSTLOGIN | 908k |
| CUSTREVIEW | 916k |
| NOTFOUND | 736k |
| PAGE | 491k |
| REVEDIT | 1200k |
| REVIEW | 684k |
| SUPERDEL | 1316k |
| TAXRATE | 1217k |
| USERERR | 1178k |

## What agents said was missing

Self-reported, so a lead to check and not a finding.

| note | runs | arms |
| --- | --- | --- |
| Configured integration-test database and fixtures | 1 | medium |
| Dedicated admin customer update integration test | 1 | medium |
| Focused endpoint integration fixtures/tests | 1 | medium |

## What agents said they could not verify

Self-reported, so a lead to check and not a finding.

| note | runs | arms |
| --- | --- | --- |
| Direct admin PUT login regression scenarios | 1 | medium |
| Direct endpoint integration responses for missing and existing items | 1 | medium |
| HTTP integration behavior | 1 | medium |

Token totals are not comparable between agents (see adapters.py). Treat a verdict as evidence only when the interval excludes 1.00, and as provisional below 8 runs per arm.

