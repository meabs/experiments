# Trial report: repo-skills

Baseline arm: **none**. Relative cost is each run's tokens divided by the baseline's mean for the same question; 1.00 means equal, lower is cheaper.

## codex

| arm | runs | correct | tokens per run (95% CI) | relative cost (95% CI) | verdict | turns | used tool | seconds | claimed vs verified |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| none | 60 | - (verified 38/60) | 376k (348k to 407k) | 1.00 | baseline | 7.5 | - | 45 | 22 overclaim, 38 agree |
| repo-skills | 60 | - (verified 40/60) | 554k (504k to 604k) | 1.51 (1.39 to 1.64) | dearer | 8.9 | 60/60 | 65 | 20 overclaim, 40 agree |

Run-to-run spread (coefficient of variation of relative cost) is 0.33. To detect a 20% difference with 80% power you would need about **44 runs per arm** (larger differences need fewer); this trial has 60.

## Tokens by question (mean, thousands)

| question | codex/none | codex/repo-skills |
| --- | --- | --- |
| ADDR | 452k | 454k |
| AMBIG | 279k | 667k |
| AVAIL | 401k | 653k |
| BOXGET | 232k | 327k |
| BOXVIS | 412k | 533k |
| CARTCALC | 305k | 501k |
| CARTLAST | 527k | 678k |
| CATCOUNT | 382k | 650k |
| CATDUP | 360k | 474k |
| CONTENT | 236k | 449k |
| CUSTDUP | 323k | 568k |
| CUSTLOGIN | 359k | 503k |
| CUSTREVIEW | 289k | 584k |
| NOTFOUND | 445k | 417k |
| PAGE | 392k | 422k |
| REVEDIT | 427k | 844k |
| REVIEW | 265k | 415k |
| SUPERDEL | 584k | 845k |
| TAXRATE | 334k | 400k |
| USERERR | 523k | 688k |

## What agents said was missing

Self-reported, so a lead to check and not a finding.

| note | runs | arms |
| --- | --- | --- |
| API integration fixture/setup | 1 | repo-skills |

## What agents said they could not verify

Self-reported, so a lead to check and not a finding.

| note | runs | arms |
| --- | --- | --- |
| Live duplicate-category API behavior | 1 | repo-skills |

Token totals are not comparable between agents (see adapters.py). Treat a verdict as evidence only when the interval excludes 1.00, and as provisional below 8 runs per arm.

