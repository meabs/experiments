# Trial report: test-skill-gate

Baseline arm: **gate**. Relative cost is each run's tokens divided by the baseline's mean for the same question; 1.00 means equal, lower is cheaper.

## codex

| arm | runs | correct | tokens per run (95% CI) | relative cost (95% CI) | verdict | turns | used tool | seconds | claimed vs verified |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gate | 60 | - (verified 47/60) | 1669k (1390k to 1958k) | 1.00 | baseline | 14.4 | - | 239 | 12 overclaim, 48 agree |

## Tokens by question (mean, thousands)

| question | codex/gate |
| --- | --- |
| ADDR | 2753k |
| AMBIG | 838k |
| AVAIL | 1699k |
| BOXGET | 1359k |
| BOXVIS | 1853k |
| CARTCALC | 2155k |
| CARTLAST | 1812k |
| CATCOUNT | 2458k |
| CATDUP | 897k |
| CONTENT | 1155k |
| CUSTDUP | 915k |
| CUSTLOGIN | 2934k |
| CUSTREVIEW | 1000k |
| NOTFOUND | 1370k |
| PAGE | 925k |
| REVEDIT | 2119k |
| REVIEW | 1049k |
| SUPERDEL | 1006k |
| TAXRATE | 1717k |
| USERERR | 3359k |

## What agents said was missing

Self-reported, so a lead to check and not a finding.

| note | runs | arms |
| --- | --- | --- |
| None | 1 | gate |

## What agents said they could not verify

Self-reported, so a lead to check and not a finding.

| note | runs | arms |
| --- | --- | --- |
| Full test suite | 1 | gate |

Token totals are not comparable between agents (see adapters.py). Treat a verdict as evidence only when the interval excludes 1.00, and as provisional below 8 runs per arm.

