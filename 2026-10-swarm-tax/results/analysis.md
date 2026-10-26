# swarm-tax: analysis

Runs: 108; tasks with all three arms: BACKINSTOCK, CARTLIMIT, DISCOUNT, PRODUCTQA, TIERPRICE, WISHLIST.

## Scores (share of hidden tests passed)

| task | solo | team | team-full | best-of-k (k=2) | best-of-k (k=4) |
| --- | --- | --- | --- | --- | --- |
| BACKINSTOCK | 0.218 | 0.179 | 0.218 | 0.218 | 0.218 |
| CARTLIMIT | 0.631 | 0.262 | 0.595 | 0.631 | 0.631 |
| DISCOUNT | 0.396 | 0.188 | 0.312 | 0.396 | 0.396 |
| PRODUCTQA | 0.917 | 0.274 | 0.548 | 0.917 | 0.917 |
| TIERPRICE | 0.381 | 0.381 | 0.690 | 0.381 | 0.381 |
| WISHLIST | 0.867 | 0.256 | 0.522 | 0.867 | 0.867 |
| **mean over tasks** | 0.568 | 0.257 | 0.481 | 0.568 | 0.568 |

k = round(mean cost of the team arm / mean cost of solo), in [2, 6]: team $0.107 / solo $0.073 gives k = 2; team-full $0.272 gives k = 4.

## Hypotheses

| # | comparison | difference | 95% interval | p | Holm p |
| --- | --- | --- | --- | --- | --- |
| H1 | team − solo (one-sided) | -0.312 | -0.408 to -0.219 | 1.0000 | 1.0000 |
| H2 | team − solo best-of-2 (two-sided) | -0.312 | -0.408 to -0.219 | 0.0000 | 0.0000 |
| H3 | team-full − team (one-sided) | 0.224 | 0.130 to 0.315 | 0.0000 | 0.0001 |

Secondary: team-full − solo best-of-4 = -0.087 (not tested).

## Cost, time, verified passes

| arm | runs | verified passes | mean cost | mean tokens | median minutes | cost per hidden test passed | timeouts |
| --- | --- | --- | --- | --- | --- | --- | --- |
| solo | 36 | 3 | $0.073 | 2.15M | 2.3 | $0.0090 | 0 |
| team | 36 | 0 | $0.107 | 3.03M | 3.9 | $0.0292 | 0 |
| team-full | 36 | 0 | $0.272 | 8.46M | 6.9 | $0.0395 | 0 |

## Did the team happen

| arm | runs | with subagents | median subagents | planner edited files | spawns not fork_turns none | review rounds (median) | mvn install | paths outside the clone |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| solo | 36 | 0 | 0.0 | — | 0 | 0.0 | 6 | 16 |
| team | 36 | 36 | 2.0 | 0 | 0 | 1.0 | 4 | 10 |
| team-full | 36 | 36 | 5.0 | 0 | 0 | 3.0 | 7 | 36 |

## Reviews

| arm | final review APPROVE | of those, hidden tests fail (rubber stamp) | any review CHANGES: mean score | first review APPROVE: mean score |
| --- | --- | --- | --- | --- |
| team | 3 | 3 | 0.262 | 0.192 |
| team-full | 18 | 18 | 0.492 | 0.536 |

## False success claims

Runs whose final report claimed success (the rig's claim check) while the independent check failed.

| arm | false passes | runs with a claim |
| --- | --- | --- |
| solo | 32 | 36 |
| team | 36 | 36 |
| team-full | 36 | 36 |
