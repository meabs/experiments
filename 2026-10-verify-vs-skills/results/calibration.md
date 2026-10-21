# Calibration (arms A and D, 2 runs per task)

Rule, fixed before calibration: keep the 20 tasks with the lowest A + D score, ties broken by the D score and then by task id. Gate: at least 8 kept tasks score 0 or 1 of 2 in D. These runs are not part of the results.

| task | kind | A (low) | D (medium) | score | kept |
| --- | --- | --- | --- | --- | --- |
| ADDR | R | 1/2 | 2/2 | 3 | yes |
| AMBIG | R | 2/2 | 2/2 | 4 | yes |
| AVAIL | R | 2/2 | 2/2 | 4 | yes |
| BOXGET | R | 2/2 | 2/2 | 4 | yes |
| BOXVIS | N | 0/2 | 2/2 | 2 | yes |
| CARTCALC | R | 2/2 | 2/2 | 4 | yes |
| CARTLAST | R | 0/2 | 2/2 | 2 | yes |
| CATCOUNT | R | 2/2 | 1/2 | 3 | yes |
| CATDUP | R | 1/2 | 2/2 | 3 | yes |
| CONTENT | R | 1/2 | 2/2 | 3 | yes |
| CUSTDUP | R | 2/2 | 2/2 | 4 | yes |
| CUSTLOGIN | R | 1/2 | 2/2 | 3 | yes |
| CUSTREVIEW | R | 1/2 | 2/2 | 3 | yes |
| HCUST | R | 2/2 | 2/2 | 4 | no |
| MANCODE | R | 2/2 | 2/2 | 4 | no |
| MANINUSE | R | 2/2 | 2/2 | 4 | no |
| MANORDER | R | 2/2 | 2/2 | 4 | no |
| NOTFOUND | R | 2/2 | 1/2 | 3 | yes |
| OPTORDER | N | 2/2 | 2/2 | 4 | no |
| PAGE | R | 1/2 | 2/2 | 3 | yes |
| PAGEVIS | N | 2/2 | 2/2 | 4 | no |
| REVEDIT | N | 0/2 | 0/2 | 0 | yes |
| REVIEW | R | 2/2 | 1/2 | 3 | yes |
| SUPERDEL | R | 1/2 | 0/2 | 1 | yes |
| TAXPAGE | R | 2/2 | 2/2 | 4 | no |
| TAXRATE | R | 0/2 | 0/2 | 0 | yes |
| USERACTIVE | R | 2/2 | 2/2 | 4 | no |
| USERERR | R | 0/2 | 0/2 | 0 | yes |

Kept tasks scoring 0 or 1 of 2 in D: 7 (gate needs 8): **not passed**.
