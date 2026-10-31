## Left-out requirements met, stage 1 (higher is better)

| Arm | Clear: ticket passed | Some: met / possible (95% CI) | Lots: met / possible (95% CI) | All S+L: met / possible | Ticket passed, all tasks |
| --- | --- | --- | --- | --- | --- |
| T | 6 of 6 | 5 / 12 (19%–68%) | 14 / 24 (39%–76%) | 19 / 36 | 17 of 18 |
| Q | 6 of 6 | 6 / 12 (25%–75%) | 15 / 24 (43%–79%) | 21 / 36 | 18 of 18 |
| G | 6 of 6 | 12 / 12 (76%–100%) | 24 / 24 (86%–100%) | 36 / 36 | 18 of 18 |
| GD | 6 of 6 | 9 / 12 (47%–91%) | 20 / 24 (64%–93%) | 29 / 36 | 18 of 18 |
| GY | 6 of 6 | 5 / 12 (19%–68%) | 13 / 24 (35%–72%) | 18 / 36 | 17 of 18 |

## By kind of requirement, Some and Lots tasks (higher is better)

| Arm | In the repo: met / possible | In my head: met / possible (95% CI) | Guessable (L2 rd) |
| --- | --- | --- | --- |
| T | 17 / 18 | 0 / 15 (0%–20%) | 2 of 3 |
| Q | 18 / 18 | 0 / 15 (0%–20%) | 3 of 3 |
| G | 18 / 18 | 15 / 15 (80%–100%) | 3 of 3 |
| GD | 18 / 18 | 9 / 15 (36%–80%) | 2 of 3 |
| GY | 17 / 18 | 0 / 15 (0%–20%) | 1 of 3 |

## Per requirement, stage 1: runs that met it, of 3 (higher is better)

| Requirement | Kind | T | Q | G | GD | GY |
| --- | --- | --- | --- | --- | --- | --- |
| S1 ra | repo | 3 | 3 | 3 | 3 | 3 |
| S1 rb | head | 0 | 0 | 3 | 0 | 0 |
| S2 ra | repo | 2 | 3 | 3 | 3 | 2 |
| S2 rb | head | 0 | 0 | 3 | 3 | 0 |
| L1 ra | repo | 3 | 3 | 3 | 3 | 3 |
| L1 rb | repo | 3 | 3 | 3 | 3 | 3 |
| L1 rc | head | 0 | 0 | 3 | 2 | 0 |
| L1 rd | head | 0 | 0 | 3 | 2 | 0 |
| L2 ra | repo | 3 | 3 | 3 | 3 | 3 |
| L2 rb | repo | 3 | 3 | 3 | 3 | 3 |
| L2 rc | head | 0 | 0 | 3 | 2 | 0 |
| L2 rd | guessable | 2 | 3 | 3 | 2 | 1 |

## Developer's cost and dialogue, stage 1 interview arms (per run, mean; lower cost is better)

| Arm | Level | Runs that asked first | Built without waiting for answers | Rounds answered | Questions asked | Words the developer read | Words the developer typed | Corrections from the brief | Point-to-repo | Stalls |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Q | Clear | 0 of 6 | 0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0 | 0 |
| Q | Some | 0 of 6 | 0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0 | 0 |
| Q | Lots | 0 of 6 | 0 | 0.0 | 0.0 | 0 | 0 | 0.0 | 0 | 0 |
| G | Clear | 6 of 6 | 0 | 2.3 | 8.2 | 486 | 17 | 0.0 | 0 | 0 |
| G | Some | 6 of 6 | 0 | 2.7 | 9.2 | 614 | 55 | 1.0 | 1 | 3 |
| G | Lots | 6 of 6 | 0 | 2.5 | 10.7 | 704 | 85 | 1.8 | 0 | 3 |
| GD | Clear | 6 of 6 | 1 | 1.2 | 4.3 | 255 | 8 | 0.0 | 0 | 1 |
| GD | Some | 6 of 6 | 3 | 1.0 | 5.0 | 247 | 25 | 0.5 | 0 | 0 |
| GD | Lots | 6 of 6 | 2 | 1.0 | 4.8 | 272 | 40 | 1.0 | 0 | 2 |
| GY | Clear | 6 of 6 | 0 | 2.0 | 8.7 | 473 | 2 | 0.0 | 0 | 0 |
| GY | Some | 6 of 6 | 0 | 1.8 | 8.5 | 502 | 2 | 0.0 | 0 | 0 |
| GY | Lots | 6 of 6 | 0 | 2.0 | 8.3 | 566 | 2 | 0.0 | 0 | 0 |

## Coverage of "in my head" requirements: did the dialogue touch it? (Q, G, GD)

| Requirement | Q touched / met | G touched / met | GD touched / met |
| --- | --- | --- | --- |
| S1 rb | 0 / 0 | 3 / 3 | 0 / 0 |
| S2 rb | 0 / 0 | 3 / 3 | 3 / 3 |
| L1 rc | 0 / 0 | 3 / 3 | 2 / 2 |
| L1 rd | 0 / 0 | 3 / 3 | 2 / 2 |
| L2 rc | 0 / 0 | 3 / 3 | 2 / 2 |
| L2 rd | 0 / 3 | 3 / 3 | 2 / 2 |

## Agent's cost, stage 1 (per run, mean; lower is better)

| Arm | Level | Wall time, min | Tokens in (k) | Tokens out (k) | Cost, $ list price |
| --- | --- | --- | --- | --- | --- |
| T | Clear | 1.0 | 261 | 3.2 | 0.013 |
| T | Some | 1.1 | 381 | 5.0 | 0.019 |
| T | Lots | 0.9 | 294 | 4.4 | 0.016 |
| Q | Clear | 1.0 | 279 | 3.6 | 0.013 |
| Q | Some | 1.1 | 366 | 4.7 | 0.017 |
| Q | Lots | 1.2 | 362 | 4.7 | 0.018 |
| G | Clear | 2.5 | 563 | 5.5 | 0.025 |
| G | Some | 6.0 | 701 | 6.9 | 0.030 |
| G | Lots | 3.3 | 621 | 6.5 | 0.027 |
| GD | Clear | 2.2 | 613 | 5.0 | 0.025 |
| GD | Some | 2.3 | 911 | 7.7 | 0.036 |
| GD | Lots | 4.7 | 836 | 7.2 | 0.034 |
| GY | Clear | 2.2 | 522 | 4.9 | 0.022 |
| GY | Some | 2.0 | 633 | 6.0 | 0.027 |
| GY | Lots | 2.5 | 593 | 6.0 | 0.027 |

## Stage 2: follow-up ticket, no developer (higher is better)

| Task | Docs: ticket passed | Docs: met / possible | No docs: ticket passed | No docs: met / possible | Carried-over rule met, docs / no docs |
| --- | --- | --- | --- | --- | --- |
| S1F | 3 of 3 | 3 / 6 | 3 of 3 | 3 / 6 | 0 / 0 |
| S2F | 3 of 3 | 3 / 6 | 3 of 3 | 3 / 6 | 0 / 0 |
| L1F | 3 of 3 | 5 / 6 | 3 of 3 | 3 / 6 | 2 / 0 |
| L2F | 3 of 3 | 6 / 9 | 3 of 3 | 6 / 9 | 0 / 0 |

## Confirmatory comparisons (stratified permutation test, 10,000 permutations, seed 1; Holm-adjusted)

| Comparison | Difference in mean per run | p | Holm p |
| --- | --- | --- | --- |
| H1: G − T, Lots, requirements met per run | +1.67 | 0.0056 | 0.0168 |
| H3a: G − GY, in-my-head requirements met per run | +1.25 | 0.0001 | 0.0004 |
| H3b: GY − T, in-my-head requirements met per run | +0.00 | 1.0000 | 1.0000 |
| H5: docs − no docs, stage 2 requirements met per run | +0.17 | 0.4052 | 0.8103 |

Total agent spend at list prices: $2.52.
