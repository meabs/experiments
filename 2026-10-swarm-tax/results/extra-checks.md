# swarm-tax: checks added after the runs

Not pre-registered (README amendment log). Descriptive only.

## 1. Best-of-k with other pickers

| task | solo mean | visible check, k=2 | own tests, k=2 | oracle, k=2 | own tests, k=4 | oracle, k=4 | team | team-full |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BACKINSTOCK | 0.218 | 0.218 | 0.218 | 0.333 | 0.218 | 0.487 | 0.179 | 0.218 |
| CARTLIMIT | 0.631 | 0.631 | 0.631 | 0.781 | 0.631 | 0.900 | 0.262 | 0.595 |
| DISCOUNT | 0.396 | 0.396 | 0.396 | 0.517 | 0.396 | 0.729 | 0.188 | 0.312 |
| PRODUCTQA | 0.917 | 0.917 | 0.917 | 0.986 | 0.917 | 1.000 | 0.274 | 0.548 |
| TIERPRICE | 0.381 | 0.381 | 0.381 | 0.610 | 0.381 | 0.876 | 0.381 | 0.690 |
| WISHLIST | 0.867 | 0.867 | 0.867 | 0.907 | 0.867 | 0.929 | 0.256 | 0.522 |
| **mean over tasks** | 0.568 | 0.568 | 0.568 | 0.689 | 0.568 | 0.820 | 0.257 | 0.481 |

Every solo run passed the visible check, so that picker equals the solo mean. k=2 matches the team arm's spend and k=4 team-full's.

Runs whose diff adds no @Test method: 108 of 108, so the own-tests picker also ties every time and equals the solo mean. Nothing a user could see separates good solo runs from bad ones here; only the oracle does.

## 2. Spec details in the diffs

| task | fields + statuses in the prompt | solo | team | team-full |
| --- | --- | --- | --- | --- |
| BACKINSTOCK | 11 + 6 | 0.82 | 0.49 | 0.69 |
| CARTLIMIT | 9 + 3 | 0.79 | 0.68 | 0.79 |
| DISCOUNT | 8 + 3 | 1.00 | 0.85 | 0.91 |
| PRODUCTQA | 10 + 5 | 0.87 | 0.66 | 0.83 |
| TIERPRICE | 2 + 3 | 0.77 | 0.60 | 0.77 |
| WISHLIST | 8 + 6 | 0.82 | 0.48 | 0.83 |
| **mean over tasks** | | 0.84 | 0.63 | 0.80 |

Correlation of spec coverage with hidden score over all 108 runs: 0.32.

## 3. Tasks won

| comparison | tasks lower | equal | higher | exact sign test, two-sided p |
| --- | --- | --- | --- | --- |
| team vs solo | 5 | 1 | 0 | 0.062 |
| team-full vs solo | 4 | 1 | 1 | 0.375 |
| team-full vs team | 0 | 0 | 6 | 0.031 |

With six tasks the smallest possible two-sided p is 0.031; this is a coarse check beside the within-task tests.
