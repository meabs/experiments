# split-spec: analysis

Runs: 144; tasks with all four arms: BACKINSTOCK, CARTLIMIT, DISCOUNT, PRODUCTQA, TIERPRICE, WISHLIST.

Scores are the share of each task's hidden tests passed, from 0 (none) to 1 (all); **higher is better**.

## Scores

| task | solo | team-spec | split-part | split-full |
| --- | --- | --- | --- | --- |
| BACKINSTOCK | 0.526 | 0.308 | 0.346 | 0.372 |
| CARTLIMIT | 0.500 | 0.464 | 0.690 | 0.774 |
| DISCOUNT | 0.333 | 0.240 | 0.490 | 0.250 |
| PRODUCTQA | 0.869 | 0.726 | 0.833 | 0.571 |
| TIERPRICE | 0.583 | 0.917 | 0.690 | 0.595 |
| WISHLIST | 0.933 | 0.578 | 0.644 | 0.611 |
| **mean over tasks** | 0.624 | 0.539 | 0.616 | 0.529 |

## Hypotheses

A difference is the first arm's score minus the second's (0.10 = 10 points of hidden tests passed); negative means the first arm did worse. Two-sided tests.

| # | comparison | difference | 95% interval | p | Holm p |
| --- | --- | --- | --- | --- | --- |
| H1 | split-part − solo | -0.008 | -0.115 to 0.093 | 0.8910 | 1.0000 |
| H2 | split-full − split-part | -0.087 | -0.206 to 0.032 | 0.1996 | 0.5987 |
| H3 | split-full − team-spec | -0.010 | -0.124 to 0.098 | 0.8796 | 1.0000 |

## Cost, time, verified passes

Cost, tokens and time: lower is better.

| arm | runs | verified passes | mean cost | mean tokens | median minutes | cost per hidden test passed | timeouts |
| --- | --- | --- | --- | --- | --- | --- | --- |
| solo | 36 | 5 | $0.073 | 2.19M | 2.3 | $0.0082 | 0 |
| team-spec | 36 | 1 | $0.117 | 3.64M | 3.9 | $0.0153 | 0 |
| split-part | 36 | 2 | $0.167 | 4.76M | 3.8 | $0.0189 | 0 |
| split-full | 36 | 3 | $0.183 | 5.36M | 3.7 | $0.0243 | 0 |

## Did the split happen

| arm | runs | median coders | runs with 2+ coders overlapping in time | median part files | planner edited source | spawns not fork_turns none | mvn install |
| --- | --- | --- | --- | --- | --- | --- | --- |
| team-spec | 36 | 1.0 | 0 | 0.0 | 0 | 0 | 3 |
| split-part | 36 | 3.0 | 36 | 3.0 | 0 | 0 | 4 |
| split-full | 36 | 3.0 | 36 | 3.0 | 0 | 0 | 2 |

## Did coders keep to their brief

split-part coders were told to read only their own part file; split-full coders to read TASK.md and their part file; the team-spec coder to read TASK.md. From each coder's own commands (a command naming the file).

| arm | coders | read TASK.md | read more than one part file | runs with a file patched by 2+ coders |
| --- | --- | --- | --- | --- |
| team-spec | 36 | 36 | 0 | 0 |
| split-part | 108 | 2 | 7 | 0 |
| split-full | 108 | 108 | 9 | 3 |

## Spec details carried through

The share of the JSON field names and HTTP statuses each task's prompt states that appear in the planner's part files and in the change (higher means more of the stated interface carried through).

| arm | in the part files | in the change |
| --- | --- | --- |
| solo | — | 0.84 |
| team-spec | — | 0.76 |
| split-part | 1.00 | 0.88 |
| split-full | 0.58 | 0.86 |

## Reviews and claims

| arm | final review APPROVE | of those, hidden tests fail | false success claims (rig's claim check) | runs with a claim |
| --- | --- | --- | --- | --- |
| solo | — | — | 28 | 36 |
| team-spec | 4 | 4 | 33 | 36 |
| split-part | 6 | 5 | 34 | 36 |
| split-full | 5 | 5 | 32 | 36 |
