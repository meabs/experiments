## In-my-head rules met, by level (rule checks: rules × 5 runs; higher is better)

| Level | Rules | T | G | S | K |
| --- | --- | --- | --- | --- | --- |
| Few, flat | 5 | 0 / 25 | 21 / 25 | 21 / 25 | 19 / 25 |
| Many, flat | 4 | 0 / 20 | 10 / 20 | 9 / 20 | 6 / 20 |
| Nested | 6 | 0 / 30 | 3 / 30 | 5 / 30 | 0 / 30 |
| **All** | 15 | 0 / 75 | 34 / 75 | 35 / 75 | 25 / 75 |

## Per rule: runs that met it, of 5 (higher is better)

| Task | Rule | Kind | T | G | S | K |
| --- | --- | --- | --- | --- | --- | --- |
| S1 | ra  | repo | 5 | 5 | 5 | 5 |
| S1 | rb support may only add internal notes | head | 0 | 2 | 1 | 0 |
| S2 | ra  | repo | 5 | 5 | 5 | 5 |
| S2 | rb resolution saved as a customer-visible comment | head | 0 | 4 | 5 | 5 |
| L1 | ra  | repo | 5 | 5 | 5 | 5 |
| L1 | rb  | repo | 5 | 5 | 5 | 3 |
| L1 | rc support can freeze, only admins unfreeze | head | 0 | 5 | 5 | 5 |
| L1 | rd audit note on freeze and unfreeze | head | 0 | 5 | 5 | 4 |
| L2 | ra  | repo | 5 | 5 | 5 | 5 |
| L2 | rb  | repo | 5 | 5 | 5 | 5 |
| L2 | rc new assignee must be assigned to the account | head | 0 | 5 | 5 | 5 |
| L2 | rd  | guessable | 5 | 5 | 5 | 5 |
| M1 | ra  | repo | 5 | 5 | 5 | 5 |
| M1 | rb  | repo | 0 | 3 | 5 | 2 |
| M1 | rc support can only lower the limit | head | 0 | 5 | 5 | 5 |
| M1 | rd £5,000 ceiling | head | 0 | 4 | 3 | 1 |
| M1 | re savings accounts fixed | head | 0 | 0 | 0 | 0 |
| M1 | rf audit note with old and new limit | head | 0 | 1 | 1 | 0 |
| N1 | ra  | repo | 5 | 5 | 5 | 5 |
| N1 | rb over £100 waits for approval (parent) | head | 0 | 1 | 2 | 0 |
| N1 | rc how approval works (child) | head | 0 | 1 | 2 | 0 |
| N1 | rd can't approve your own (child) | head | 0 | 1 | 1 | 0 |
| N2 | ra  | repo | 5 | 5 | 5 | 5 |
| N2 | rb  | repo | 5 | 5 | 5 | 5 |
| N2 | rc money must be moved first (parent) | head | 0 | 0 | 0 | 0 |
| N2 | rd where the money can go (child) | head | 0 | 0 | 0 | 0 |
| N2 | re the move is booked on both accounts (child) | head | 0 | 0 | 0 | 0 |

## All left-out requirements and ticket pass (higher is better)

| Arm | All left-out: met / possible | Ticket passed |
| --- | --- | --- |
| T | 55 / 135 | 35 of 35 |
| G | 92 / 135 | 35 of 35 |
| S | 95 / 135 | 35 of 35 |
| K | 80 / 135 | 35 of 35 |

## Why a rule was missed (in-my-head rules, interview arms)

| Arm | Rule checks | Met | Missed: never raised | Missed: raised but built wrong | Wrong recommendations corrected |
| --- | --- | --- | --- | --- | --- |
| G | 75 | 34 | 41 | 0 | 26 |
| S | 75 | 35 | 39 | 1 | 34 |
| K | 75 | 25 | 50 | 0 | 0 |

## Coverage per in-my-head rule: runs whose dialogue touched it / runs that met it (of 5)

| Task | Rule | G touched / met | S touched / met | K touched / met |
| --- | --- | --- | --- | --- |
| S1 | rb support may only add internal notes | 2 / 2 | 1 / 1 | 0 / 0 |
| S2 | rb resolution saved as a customer-visible comment | 4 / 4 | 5 / 5 | 5 / 5 |
| L1 | rc support can freeze, only admins unfreeze | 5 / 5 | 5 / 5 | 5 / 5 |
| L1 | rd audit note on freeze and unfreeze | 5 / 5 | 5 / 5 | 4 / 4 |
| L2 | rc new assignee must be assigned to the account | 5 / 5 | 5 / 5 | 5 / 5 |
| M1 | rc support can only lower the limit | 5 / 5 | 5 / 5 | 5 / 5 |
| M1 | rd £5,000 ceiling | 4 / 4 | 3 / 3 | 1 / 1 |
| M1 | re savings accounts fixed | 0 / 0 | 0 / 0 | 0 / 0 |
| M1 | rf audit note with old and new limit | 1 / 1 | 1 / 1 | 0 / 0 |
| N1 | rb over £100 waits for approval (parent) | 1 / 1 | 3 / 2 | 0 / 0 |
| N1 | rc how approval works (child) | 1 / 1 | 2 / 2 | 0 / 0 |
| N1 | rd can't approve your own (child) | 1 / 1 | 1 / 1 | 0 / 0 |
| N2 | rc money must be moved first (parent) | 0 / 0 | 0 / 0 | 0 / 0 |
| N2 | rd where the money can go (child) | 0 / 0 | 0 / 0 | 0 / 0 |
| N2 | re the move is booked on both accounts (child) | 0 / 0 | 0 / 0 | 0 / 0 |

## Developer's cost and dialogue (per run, mean; lower cost is better)

| Arm | Level | Never waited for an answer | Rounds answered | Questions asked | Words the developer read | Words the developer typed | Corrections | Point-to-repo | Stalls |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G | Few, flat | 0 of 20 | 2.4 | 9.9 | 599 | 57 | 1.0 | 1 | 2 |
| G | Many, flat | 0 of 5 | 2.6 | 10.8 | 668 | 70 | 2.4 | 0 | 0 |
| G | Nested | 0 of 10 | 2.6 | 12.7 | 718 | 34 | 0.1 | 0 | 5 |
| S | Few, flat | 0 of 20 | 1.0 | 7.8 | 293 | 45 | 1.1 | 0 | 1 |
| S | Many, flat | 0 of 5 | 1.0 | 8.0 | 266 | 60 | 2.4 | 0 | 0 |
| S | Nested | 0 of 10 | 1.2 | 10.4 | 351 | 39 | 0.5 | 0 | 0 |
| K | Few, flat | 0 of 20 | 1.0 | 3.0 | 72 | 51 | 0.0 | 3 | 0 |
| K | Many, flat | 0 of 5 | 1.0 | 3.0 | 101 | 42 | 0.0 | 0 | 0 |
| K | Nested | 0 of 10 | 1.0 | 3.0 | 70 | 27 | 0.0 | 0 | 0 |

## Agent's cost (per run, mean; lower is better)

| Arm | Level | Wall time, min | Tokens in (k) | Tokens out (k) | Cost, $ list price |
| --- | --- | --- | --- | --- | --- |
| T | Few, flat | 1.1 | 322 | 4.4 | 0.016 |
| T | Many, flat | 1.1 | 383 | 4.3 | 0.017 |
| T | Nested | 1.0 | 319 | 4.9 | 0.016 |
| G | Few, flat | 2.9 | 590 | 6.0 | 0.026 |
| G | Many, flat | 2.8 | 737 | 6.6 | 0.031 |
| G | Nested | 3.6 | 600 | 6.2 | 0.026 |
| S | Few, flat | 1.7 | 386 | 5.7 | 0.019 |
| S | Many, flat | 1.4 | 435 | 5.1 | 0.019 |
| S | Nested | 1.7 | 401 | 6.0 | 0.021 |
| K | Few, flat | 1.4 | 370 | 4.7 | 0.017 |
| K | Many, flat | 1.2 | 284 | 3.9 | 0.014 |
| K | Nested | 1.8 | 428 | 5.2 | 0.019 |

## Hypothesis 1: S against G on flat tickets (non-inferiority, margin −0.15)

| Difference S − G, mean over 9 rules of the proportion of runs meeting the rule | One-sided 95% lower bound | Non-inferior? |
| --- | --- | --- |
| -0.022 | -0.133 | yes |

## Hypotheses 2–4 (stratified permutation test, 10,000 permutations, seed 1; Holm-adjusted)

| Comparison | Difference in mean per run | p | Holm p |
| --- | --- | --- | --- |
| H2: G − S, nested tickets, in-my-head rules met per run | -0.20 | 1.0000 | 1.0000 |
| H3: G − K, M1 + nested tickets, in-my-head rules met per run | +0.47 | 0.0845 | 0.1690 |
| H4a: S − G, words the developer read per run | -336.83 | 0.0001 | 0.0004 |
| H4b: K − G, words the developer read per run | -567.23 | 0.0001 | 0.0004 |

## Description: in-my-head rules met per run, mean (higher is better)

| Level | T | G | S | K |
| --- | --- | --- | --- | --- |
| Few, flat | 0.00 | 1.05 | 1.05 | 0.95 |
| Many, flat | 0.00 | 2.00 | 1.80 | 1.20 |
| Nested | 0.00 | 0.30 | 0.50 | 0.00 |

Total agent spend at list prices: $2.81.
