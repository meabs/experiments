# Trial report: test-skill

Baseline arm: **none**. Relative cost is each run's tokens divided by the baseline's mean for the same question; 1.00 means equal, lower is cheaper.

## codex

| arm | runs | correct | tokens per run (95% CI) | relative cost (95% CI) | verdict | turns | used tool | seconds | claimed vs verified |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| none | 60 | - (verified 40/60) | 440k (397k to 490k) | 1.00 | baseline | 7.3 | - | 57 | 20 overclaim, 40 agree |
| instruction | 60 | - (verified 41/60) | 1330k (1087k to 1620k) | 3.05 (2.53 to 3.71) | dearer | 12.1 | - | 142 | 16 overclaim, 44 agree |
| skill | 60 | - (verified 41/60) | 1775k (1433k to 2165k) | 4.02 (3.34 to 4.84) | dearer | 15.2 | 60/60 | 167 | 13 overclaim, 1 underclaim, 46 agree |
| skill-revised | 60 | - (verified 43/60) | 1776k (1404k to 2195k) | 3.88 (3.24 to 4.58) | dearer | 13.7 | 60/60 | 161 | 14 overclaim, 1 underclaim, 45 agree |

Run-to-run spread (coefficient of variation of relative cost) is 0.75. To detect a 20% difference with 80% power you would need about **219 runs per arm** (larger differences need fewer); this trial has 60.

## Tokens by question (mean, thousands)

| question | codex/instruction | codex/none | codex/skill | codex/skill-revised |
| --- | --- | --- | --- | --- |
| ADDR | 3301k | 403k | 2825k | 1782k |
| AMBIG | 607k | 295k | 1042k | 1134k |
| AVAIL | 825k | 411k | 842k | 764k |
| BOXGET | 878k | 412k | 1503k | 1463k |
| BOXVIS | 1262k | 321k | 965k | 995k |
| CARTCALC | 1275k | 391k | 1324k | 1198k |
| CARTLAST | 836k | 478k | 1000k | 1446k |
| CATCOUNT | 2065k | 409k | 1037k | 956k |
| CATDUP | 890k | 422k | 1194k | 866k |
| CONTENT | 590k | 299k | 758k | 803k |
| CUSTDUP | 729k | 680k | 726k | 799k |
| CUSTLOGIN | 1032k | 373k | 1145k | 788k |
| CUSTREVIEW | 997k | 478k | 5239k | 3293k |
| NOTFOUND | 2190k | 596k | 1625k | 2217k |
| PAGE | 912k | 369k | 1147k | 850k |
| REVEDIT | 1250k | 668k | 2692k | 4898k |
| REVIEW | 755k | 392k | 3090k | 1961k |
| SUPERDEL | 966k | 376k | 1155k | 1625k |
| TAXRATE | 1813k | 497k | 1828k | 2826k |
| USERERR | 3429k | 535k | 4359k | 4849k |

## What agents said was missing

Self-reported, so a lead to check and not a finding.

| note | runs | arms |
| --- | --- | --- |
| A focused content-box endpoint test or fixture | 1 | none |
| Content-box API test fixture | 1 | none |

## What agents said they could not verify

Self-reported, so a lead to check and not a finding.

| note | runs | arms |
| --- | --- | --- |
| Runtime API behavior and automated tests | 2 | none |

Token totals are not comparable between agents (see adapters.py). Treat a verdict as evidence only when the interval excludes 1.00, and as provisional below 8 runs per arm.

