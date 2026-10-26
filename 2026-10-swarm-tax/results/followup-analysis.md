# swarm-tax follow-up: shared spec

Runs: 108; tasks with all three arms: BACKINSTOCK, CARTLIMIT, DISCOUNT, PRODUCTQA, TIERPRICE, WISHLIST.

| task | solo | team | team-spec |
| --- | --- | --- | --- |
| BACKINSTOCK | 0.218 | 0.179 | 0.308 |
| CARTLIMIT | 0.631 | 0.262 | 0.679 |
| DISCOUNT | 0.396 | 0.188 | 0.229 |
| PRODUCTQA | 0.917 | 0.274 | 0.762 |
| TIERPRICE | 0.381 | 0.381 | 0.536 |
| WISHLIST | 0.867 | 0.256 | 0.733 |
| **mean over tasks** | 0.568 | 0.257 | 0.541 |

## Hypotheses

| # | comparison | difference | 95% interval | p | Holm p |
| --- | --- | --- | --- | --- | --- |
| H4 | team-spec − team (one-sided) | 0.285 | 0.184 to 0.382 | 0.0000 | 0.0000 |
| H5 | team-spec − solo (two-sided) | -0.027 | -0.137 to 0.082 | 0.6653 | 0.6653 |

## Secondary

| arm | runs | mean cost | spec details in diff | final APPROVE | of those, hidden tests fail | coder read TASK.md | reviewer read TASK.md |
| --- | --- | --- | --- | --- | --- | --- | --- |
| solo | 36 | $0.073 | 0.84 | — | — | — | — |
| team | 36 | $0.107 | 0.63 | 3 | 3 | — | — |
| team-spec | 36 | $0.116 | 0.80 | 3 | 3 | 36 | 36 |
