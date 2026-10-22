# verify-vs-skills: analysis

240 runs over 20 tasks; statuses: {'ok': 240}.

## Passes per task (of 3)

| task | kind | A none (low) | B verify (low) | C superpowers (low) | D medium (no skills) |
| --- | --- | --- | --- | --- | --- |
| ADDR | R | 1 | 3 | 2 | 3 |
| AMBIG | R | 3 | 3 | 3 | 3 |
| AVAIL | R | 3 | 3 | 3 | 3 |
| BOXGET | R | 3 | 3 | 3 | 3 |
| BOXVIS | N | 0 | 1 | 1 | 2 |
| CARTCALC | R | 3 | 2 | 2 | 3 |
| CARTLAST | R | 2 | 2 | 0 | 3 |
| CATCOUNT | R | 1 | 1 | 0 | 3 |
| CATDUP | R | 3 | 3 | 3 | 3 |
| CONTENT | R | 3 | 2 | 2 | 3 |
| CUSTDUP | R | 3 | 2 | 3 | 3 |
| CUSTLOGIN | R | 2 | 3 | 3 | 3 |
| CUSTREVIEW | R | 1 | 1 | 0 | 3 |
| NOTFOUND | R | 1 | 3 | 2 | 3 |
| PAGE | R | 3 | 1 | 2 | 3 |
| REVEDIT | N | 0 | 0 | 0 | 0 |
| REVIEW | R | 3 | 3 | 3 | 1 |
| SUPERDEL | R | 1 | 3 | 3 | 2 |
| TAXRATE | R | 0 | 0 | 2 | 2 |
| USERERR | R | 0 | 0 | 0 | 0 |
| **total** | | **36/60** | **39/60** | **37/60** | **49/60** |

## Hypotheses (preregistered)

| # | arm vs none | tasks better / same / worse | mean per-task difference in pass rate (95% CI) | p (one-sided) | Holm p |
| --- | --- | --- | --- | --- | --- |
| H1 | verify | 5 / 11 / 4 | +5.0 pts (-10.0 to +20.0) | 0.336 | 0.672 |
| H2 | medium | 9 / 10 / 1 | +21.7 pts (+5.0 to +36.7) | 0.014 | 0.041 |
| H3 | superpowers | 6 / 8 / 6 | +1.7 pts (-13.3 to +16.7) | 0.500 | 0.672 |

**H4** (reported, not tested): cost per verified pass, `verify` over `superpowers` = 0.60 (95% CI 0.47 to 0.73, resampling tasks).

**H5** (secondary, unadjusted): neighbour-break tasks (2): runs with a failing keeps... test, none 3 against verify 5; one-sided sign-flip p = 1.000.

Selection used the calibration runs of arms A and D, which favours those two arms slightly (regression to the mean): conservative for H1 and H3, and in D's favour when D is compared with B or C.

## Secondary comparisons (two-sided, unadjusted)

| comparison | tasks better / same / worse | mean per-task difference in pass rate (95% CI) | p |
| --- | --- | --- | --- |
| verify vs superpowers | 5 / 12 / 3 | +3.3 pts (-8.3 to +15.0) | 0.797 |
| verify vs medium | 2 / 9 / 9 | -16.7 pts (-31.7 to -1.7) | 0.075 |
| superpowers vs medium | 2 / 9 / 9 | -20.0 pts (-38.3 to -1.7) | 0.073 |

## Cost, time and process

| arm | runs | verified passes | mean tokens | total $ | $ per verified pass | minutes per verified pass | median s | ran Maven tests | wrote tests | API-level test written | started or called the app | test-file-first | confirmed TDD | neighbour breaks | false success claims (of failed) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A none (low) | 60 | 36 | 0.41M | 1.00 | 0.028 | 1.4 | 48 | 3 | 0 | 0 | 0 | 0 | 0 | 3 | 24/24 |
| B verify (low) | 60 | 39 | 0.75M | 1.62 | 0.042 | 2.2 | 81 | 23 | 5 | 5 | 48 | 0 | 0 | 5 | 20/21 |
| C superpowers (low) | 60 | 37 | 1.29M | 2.57 | 0.070 | 3.1 | 112 | 48 | 43 | 16 | 0 | 40 | 31 | 3 | 23/23 |
| D medium (no skills) | 60 | 49 | 0.89M | 1.95 | 0.040 | 2.0 | 96 | 37 | 1 | 1 | 0 | 0 | 0 | 4 | 11/11 |

## Exploratory: by kind of task

| kind | tasks | A none (low) | B verify (low) | C superpowers (low) | D medium (no skills) |
| --- | --- | --- | --- | --- | --- |
| N | 2 | 0/6 | 1/6 | 1/6 | 2/6 |
| R | 18 | 36/54 | 38/54 | 36/54 | 47/54 |

Total estimated spend (list prices): $7.14.

## Added after the results (exploratory)

| arm | tried to start the app | app came up | called it successfully | runs stating something unchecked | failed runs claiming success |
| --- | --- | --- | --- | --- | --- |
| A none (low) | 0/60 | 0 | 0 | 60/60 | 24/24 |
| B verify (low) | 47/60 | 2 | 3 | 57/60 | 20/21 |
| C superpowers (low) | 0/60 | 0 | 0 | 55/60 | 23/23 |
| D medium (no skills) | 0/60 | 0 | 0 | 59/60 | 11/11 |
