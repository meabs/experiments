# Trial report: explicit-skills

Baseline arm: **none**. Relative cost is each run's tokens divided by the baseline's mean for the same question; 1.00 means equal, lower is cheaper.

## codex

| arm | runs | correct | tokens per run (95% CI) | relative cost (95% CI) | verdict | turns | used tool | seconds | claimed vs verified |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| none | 60 | - (verified 37/60) | 398k (367k to 432k) | 1.00 | baseline | 7.5 | - | 55 | 23 overclaim, 37 agree |
| discover | 60 | - (verified 39/60) | 561k (517k to 606k) | 1.44 (1.33 to 1.57) | dearer | 8.4 | 60/60 | 75 | 21 overclaim, 39 agree |
| explicit | 60 | - (verified 42/60) | 1098k (968k to 1263k) | 2.80 (2.49 to 3.16) | dearer | 11.0 | 60/60 | 123 | 18 overclaim, 42 agree |

Run-to-run spread (coefficient of variation of relative cost) is 0.56. To detect a 20% difference with 80% power you would need about **126 runs per arm** (larger differences need fewer); this trial has 60.

## Tokens by question (mean, thousands)

| question | codex/discover | codex/explicit | codex/none |
| --- | --- | --- | --- |
| ADDR | 501k | 1210k | 441k |
| AMBIG | 567k | 1196k | 381k |
| AVAIL | 601k | 1063k | 266k |
| BOXGET | 413k | 503k | 233k |
| BOXVIS | 396k | 863k | 354k |
| CARTCALC | 697k | 1360k | 579k |
| CARTLAST | 560k | 1234k | 329k |
| CATCOUNT | 510k | 1001k | 411k |
| CATDUP | 798k | 1219k | 397k |
| CONTENT | 294k | 877k | 251k |
| CUSTDUP | 473k | 879k | 478k |
| CUSTLOGIN | 587k | 1011k | 494k |
| CUSTREVIEW | 537k | 767k | 364k |
| NOTFOUND | 568k | 1201k | 497k |
| PAGE | 576k | 790k | 335k |
| REVEDIT | 680k | 920k | 431k |
| REVIEW | 583k | 1087k | 433k |
| SUPERDEL | 685k | 1039k | 449k |
| TAXRATE | 530k | 1395k | 357k |
| USERERR | 659k | 2351k | 489k |

## What agents said was missing

Self-reported, so a lead to check and not a finding.

| note | runs | arms |
| --- | --- | --- |
| A focused content-box integration test or fixture | 1 | discover |
| Cart integration test fixture/environment | 1 | none |
| Dedicated content-box endpoint tests or fixtures | 1 | none |

## What agents said they could not verify

Self-reported, so a lead to check and not a finding.

| note | runs | arms |
| --- | --- | --- |
| End-to-end API behavior | 1 | none |
| Full mvn -o test was not run | 1 | explicit |
| Live HTTP behavior | 1 | discover |
| Runtime HTTP behavior and automated tests | 1 | none |

Token totals are not comparable between agents (see adapters.py). Treat a verdict as evidence only when the interval excludes 1.00, and as provisional below 8 runs per arm.

