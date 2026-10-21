## Pass rate by cell

| task | agent | none | placebo | superpowers | pocock | pstack |
| --- | --- | --- | --- | --- | --- | --- |
| BUG | codex | 6/6 | 4/6 | 6/6 | 5/6 | - |
| BUG | cursor | 6/6 | 6/6 | 6/6 | 5/6 | 6/6 |
| CROSS | codex | 4/6 | 4/6 | 6/6 | 4/6 | - |
| CROSS | cursor | 6/6 | 6/6 | 6/6 | 5/6 | 6/6 |
| FEAT | codex | 6/6 | 6/6 | 6/6 | 6/6 | - |
| FEAT | cursor | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |

## Hypotheses

| # | comparison | treatment | none | one-sided Fisher p | supported |
| --- | --- | --- | --- | --- | --- |
| H1 | superpowers pass, BUG+CROSS, both agents | 24/24 | 22/24 | 0.245 | no |
| H2 | pocock pass, BUG+CROSS, both agents | 19/24 | 22/24 | 0.951 | no |
| H7 | pstack pass, all tasks, Cursor | 18/18 | 18/18 | 1.000 | no |
| (ctrl) | placebo pass, BUG+CROSS, both agents | 20/24 | 22/24 | 0.906 | no |
| H4 | superpowers: BUG runs with a test that bites | 12/12 | 8/12 | 0.047 | yes |
| H4 | pocock: BUG runs with a test that bites | 12/12 | 8/12 | 0.047 | yes |
| H4 | pstack: BUG runs with a test that bites | 5/6 | 8/12 | 0.439 | no |
| H5 | superpowers: test-file-first, share of all change runs | 31/36 | 0/36 | 0.000 | yes |
| H5 | pocock: test-file-first, share of all change runs | 10/36 | 0/36 | 0.000 | yes |
| H5 | pstack: test-file-first, share of all change runs | 6/18 | 0/18 | 0.010 | yes |
| H5 | placebo: test-file-first, share of all change runs | 0/36 | 0/36 | 1.000 | no |
| (H5b) | superpowers: test-file-first, only runs that edited both test and main | 31/35 | 0/10 | 0.000 | yes |
| (H5b) | pocock: test-file-first, only runs that edited both test and main | 10/22 | 0/10 | 0.010 | yes |
| (H5b) | pstack: test-file-first, only runs that edited both test and main | 6/13 | 0/2 | 0.343 | no |
| (H5b) | placebo: test-file-first, only runs that edited both test and main | 0/11 | 0/10 | 1.000 | no |

## Per arm and agent (all tasks)

| agent | arm | pass | median tokens | tokens vs none | mean $ | skill read | added tests | test-file-first | overclaims | median diff lines | median s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex | none | 16/18 | 1.67M | 1.00x | 0.076 | 0/18 | 7/18 | 0/8 | 2 | 82 | 134 |
| codex | placebo | 14/18 | 2.20M | 1.25x | 0.087 | 18/18 | 9/18 | 0/9 | 3 | 82 | 161 |
| codex | superpowers | 18/18 | 6.04M | 2.77x | 0.175 | 18/18 | 17/18 | 17/17 | 0 | 166 | 307 |
| codex | pocock | 15/18 | 2.98M | 1.74x | 0.098 | 7/18 | 13/18 | 7/13 | 3 | 84 | 192 |
| cursor | none | 18/18 | 0.41M | 1.00x | 1.072 | 0/18 | 2/18 | 0/2 | 0 | 55 | 118 |
| cursor | placebo | 18/18 | 0.47M | 1.05x | 1.010 | 18/18 | 2/18 | 0/2 | 0 | 44 | 116 |
| cursor | superpowers | 18/18 | 0.86M | 2.33x | 1.993 | 18/18 | 18/18 | 14/18 | 0 | 128 | 170 |
| cursor | pocock | 16/18 | 0.69M | 1.49x | 1.363 | 11/18 | 9/18 | 3/9 | 1 | 66 | 149 |
| cursor | pstack | 18/18 | 1.20M | 2.75x | 2.420 | 18/18 | 12/18 | 6/13 | 0 | 96 | 206 |

## Per cell detail

| task | agent | arm | pass | hidden pass | other failures (runs) | overclaims | skill read | mean $ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BUG | codex | none | 6/6 | 6/6 | 0 | 0 | 0/6 | 0.044 |
| BUG | codex | placebo | 4/6 | 4/6 | 0 | 2 | 6/6 | 0.045 |
| BUG | codex | superpowers | 6/6 | 6/6 | 0 | 0 | 6/6 | 0.084 |
| BUG | codex | pocock | 5/6 | 5/6 | 0 | 1 | 6/6 | 0.060 |
| BUG | cursor | none | 6/6 | 6/6 | 0 | 0 | 0/6 | 0.839 |
| BUG | cursor | placebo | 6/6 | 6/6 | 0 | 0 | 6/6 | 0.562 |
| BUG | cursor | superpowers | 6/6 | 6/6 | 0 | 0 | 6/6 | 1.474 |
| BUG | cursor | pocock | 5/6 | 5/6 | 0 | 1 | 6/6 | 1.430 |
| BUG | cursor | pstack | 6/6 | 6/6 | 0 | 0 | 6/6 | 2.502 |
| CROSS | codex | none | 4/6 | 4/6 | 0 | 2 | 0/6 | 0.082 |
| CROSS | codex | placebo | 4/6 | 5/6 | 1 | 1 | 6/6 | 0.099 |
| CROSS | codex | superpowers | 6/6 | 6/6 | 0 | 0 | 6/6 | 0.205 |
| CROSS | codex | pocock | 4/6 | 5/6 | 1 | 2 | 0/6 | 0.116 |
| CROSS | cursor | none | 6/6 | 6/6 | 0 | 0 | 0/6 | 0.734 |
| CROSS | cursor | placebo | 6/6 | 6/6 | 0 | 0 | 6/6 | 0.938 |
| CROSS | cursor | superpowers | 6/6 | 6/6 | 0 | 0 | 6/6 | 1.623 |
| CROSS | cursor | pocock | 5/6 | 5/6 | 0 | 0 | 1/6 | 0.848 |
| CROSS | cursor | pstack | 6/6 | 6/6 | 0 | 0 | 6/6 | 1.563 |
| FEAT | codex | none | 6/6 | 6/6 | 0 | 0 | 0/6 | 0.102 |
| FEAT | codex | placebo | 6/6 | 6/6 | 0 | 0 | 6/6 | 0.117 |
| FEAT | codex | superpowers | 6/6 | 6/6 | 0 | 0 | 6/6 | 0.237 |
| FEAT | codex | pocock | 6/6 | 6/6 | 0 | 0 | 1/6 | 0.117 |
| FEAT | cursor | none | 6/6 | 6/6 | 0 | 0 | 0/6 | 1.643 |
| FEAT | cursor | placebo | 6/6 | 6/6 | 0 | 0 | 6/6 | 1.530 |
| FEAT | cursor | superpowers | 6/6 | 6/6 | 0 | 0 | 6/6 | 2.883 |
| FEAT | cursor | pocock | 6/6 | 6/6 | 0 | 0 | 4/6 | 1.811 |
| FEAT | cursor | pstack | 6/6 | 6/6 | 0 | 0 | 6/6 | 3.195 |

Total spend: $149.29 (codex $7.85, cursor $141.45 with no cache discount, as in the design)
