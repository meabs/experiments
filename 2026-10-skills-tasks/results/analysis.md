# skills-tasks: analysis

128 runs over 16 tasks; statuses: {'ok': 128}.

## Passes per task (of 2)

| task | kind | none | placebo | superpowers | pocock |
| --- | --- | --- | --- | --- | --- |
| ADDR | real bug | 1 | 1 | 0 | 1 |
| AMBIG | real bug | 2 | 2 | 2 | 2 |
| AVAIL | real bug | 2 | 2 | 2 | 2 |
| CARTCALC | planted bug | 2 | 2 | 1 | 2 |
| CATCOUNT | feature | 2 | 0 | 2 | 1 |
| CATDUP | real bug | 2 | 2 | 2 | 2 |
| CONTENT | real bug | 1 | 2 | 2 | 2 |
| CUSTDUP | real bug | 2 | 1 | 2 | 2 |
| HCUST | feature | 1 | 2 | 1 | 2 |
| HREVIEW | real bug | 0 | 0 | 0 | 0 |
| MANCODE | feature | 2 | 2 | 2 | 2 |
| MANINUSE | real bug | 2 | 2 | 2 | 2 |
| MANORDER | feature | 2 | 2 | 2 | 2 |
| NOTFOUND | real bug | 1 | 1 | 1 | 2 |
| PAGE | real bug | 2 | 2 | 1 | 2 |
| TAXRATE | feature | 0 | 0 | 2 | 1 |
| **total** | | **24/32** | **23/32** | **24/32** | **27/32** |

## Hypotheses (preregistered)

| # | pack vs none | tasks better / same / worse | mean per-task difference in pass rate (95% CI) | p | Holm p |
| --- | --- | --- | --- | --- | --- |
| T1 | superpowers | 2 / 11 / 3 | +0.0 pts (-15.6 to +18.8) | 0.625 | 0.625 |
| T2 | pocock | 4 / 11 / 1 | +9.4 pts (-3.1 to +21.9) | 0.188 | 0.375 |
| T3 | placebo | 2 / 12 / 2 | -3.1 pts (-21.9 to +12.5) | 1.000 (two-sided) | - |

A pack's gain counts as a pack effect only if it exceeds the placebo's (T3).

## Cost and process (all tasks)

| arm | runs | mean tokens | per-task token ratio vs none (95% CI) | mean $ | median s | median Maven test runs | median production / test lines | skill read | test-file-first | confirmed TDD | unknown TDD | overclaims |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| none | 32 | 0.37M | 1.00 (1.00 to 1.00) | 0.016 | 43 | 0 | 13 / 0 | 0/32 | 0/32 | 0/32 | 0 | 7 |
| placebo | 32 | 0.40M | 1.09 (0.96 to 1.22) | 0.017 | 47 | 0 | 20 / 0 | 32/32 | 0/32 | 0/32 | 0 | 9 |
| superpowers | 32 | 1.09M | 3.07 (2.50 to 3.68) | 0.038 | 105 | 3 | 24 / 24 | 32/32 | 21/32 | 9/32 | 4 | 7 |
| pocock | 32 | 0.54M | 1.57 (1.10 to 2.24) | 0.021 | 54 | 0 | 16 / 0 | 27/32 | 1/32 | 0/32 | 0 | 5 |

## Exploratory: by kind of task

| kind | tasks | none | placebo | superpowers | pocock |
| --- | --- | --- | --- | --- | --- |
| real bug | 10 | 15/20 | 15/20 | 14/20 | 17/20 |
| planted bug | 1 | 2/2 | 2/2 | 1/2 | 2/2 |
| feature | 5 | 7/10 | 6/10 | 9/10 | 8/10 |

Total estimated spend (list prices): $2.95.
