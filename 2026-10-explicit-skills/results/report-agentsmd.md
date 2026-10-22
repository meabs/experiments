# Trial report: explicit-skills-agentsmd

Baseline arm: **agentsmd**. Relative cost is each run's tokens divided by the baseline's mean for the same question; 1.00 means equal, lower is cheaper.

## codex

| arm | runs | correct | tokens per run (95% CI) | relative cost (95% CI) | verdict | turns | used tool | seconds | claimed vs verified |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agentsmd | 60 | - (verified 43/60) | 992k (916k to 1072k) | 1.00 | baseline | 10.3 | 60/60 | 121 | 17 overclaim, 1 underclaim, 41 agree, 1 none |

## Tokens by question (mean, thousands)

| question | codex/agentsmd |
| --- | --- |
| ADDR | 878k |
| AMBIG | 1073k |
| AVAIL | 1058k |
| BOXGET | 540k |
| BOXVIS | 1041k |
| CARTCALC | 756k |
| CARTLAST | 1149k |
| CATCOUNT | 1231k |
| CATDUP | 989k |
| CONTENT | 755k |
| CUSTDUP | 1215k |
| CUSTLOGIN | 993k |
| CUSTREVIEW | 924k |
| NOTFOUND | 809k |
| PAGE | 1293k |
| REVEDIT | 911k |
| REVIEW | 807k |
| SUPERDEL | 1138k |
| TAXRATE | 1252k |
| USERERR | 1027k |

## What agents said was missing

Self-reported, so a lead to check and not a finding.

| note | runs | arms |
| --- | --- | --- |
| Completed integration-test result | 1 | agentsmd |

## What agents said they could not verify

Self-reported, so a lead to check and not a finding.

| note | runs | arms |
| --- | --- | --- |
| Maven checks did not complete within the available run window | 1 | agentsmd |

Token totals are not comparable between agents (see adapters.py). Treat a verdict as evidence only when the interval excludes 1.00, and as provisional below 8 runs per arm.

