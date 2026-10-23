# diff-judge: analysis

288 judgements ({('hosted', 'claim'): 96, ('hosted', 'diff'): 96, ('hosted', 'hedge'): 96}), 24 repeated; 12 tasks. Replies without a verdict: {}; timeouts: 0.

## Totals

| model | arm | caught (failing judged FAIL) | accepted (passing judged PASS) | balanced accuracy | no verdict |
| --- | --- | --- | --- | --- | --- |
| hosted | diff | 21/48 | 36/48 | 0.594 | 0 |
| hosted | claim | 20/48 | 34/48 | 0.562 | 0 |
| hosted | hedge | 30/48 | 22/48 | 0.542 | 0 |

The agents' own reports flagged 1 of these 48 failing changes (claimed anything other than 'passed').

## Hypotheses (preregistered)

| # | comparison | tasks better / same / worse | mean per-task effect (95% CI) | p | Holm p |
| --- | --- | --- | --- | --- | --- |
| H1 | hosted, diff: balanced accuracy vs 0.5 | 6 / 4 / 2 | +9.4 pts (+1.0 to +19.8) | 0.070 | 0.141 |
| H2 | hosted: catch rate, diff vs claim | 2 / 9 / 1 | +2.1 pts (-4.2 to +8.3) | 0.500 | 0.500 |
| H3 | hosted, diff: catch rate vs the agents' own reports | 9 / 3 / 0 | +41.7 pts (+22.9 to +62.5) | 0.002 | 0.006 |

## Secondary (two-sided, unadjusted)

| comparison | tasks better / same / worse | mean per-task effect (95% CI) | p |
| --- | --- | --- | --- |
| hosted: catch rate, hedge vs claim | 7 / 5 / 0 | +20.8 pts (+8.3 to +35.4) | 0.016 |
| hosted: accept rate, hedge vs claim | 1 / 3 / 8 | -25.0 pts (-37.5 to -10.4) | 0.020 |
| hosted: accept rate, diff vs claim | 4 / 6 / 2 | +4.2 pts (-10.4 to +18.8) | 0.781 |

## Per task (caught of 4 / accepted of 4)

| task | hosted diff | hosted claim | hosted hedge |
| --- | --- | --- | --- |
| ADDR | 1 / 2 | 0 / 4 | 2 / 2 |
| BOXVIS | 3 / 2 | 3 / 2 | 3 / 1 |
| CARTCALC | 0 / 4 | 0 / 4 | 1 / 2 |
| CARTLAST | 0 / 3 | 1 / 4 | 2 / 2 |
| CATCOUNT | 3 / 1 | 3 / 1 | 3 / 0 |
| CONTENT | 2 / 4 | 1 / 4 | 2 / 4 |
| CUSTLOGIN | 1 / 3 | 1 / 2 | 4 / 2 |
| CUSTREVIEW | 4 / 1 | 4 / 0 | 4 / 0 |
| NOTFOUND | 2 / 4 | 2 / 2 | 2 / 0 |
| PAGE | 1 / 4 | 1 / 4 | 2 / 3 |
| SUPERDEL | 0 / 4 | 0 / 4 | 1 / 2 |
| TAXRATE | 4 / 4 | 4 / 3 | 4 / 4 |

## By failure kind (failing items judged FAIL)

| model | arm | existing tests broken | hidden tests fail | neighbour break |
| --- | --- | --- | --- | --- |
| hosted | diff | 2/8 | 16/36 | 3/4 |
| hosted | claim | 2/8 | 15/36 | 3/4 |
| hosted | hedge | 3/8 | 24/36 | 3/4 |

## Confidence

| model | arm | mean confidence when right | when wrong | accuracy at confidence >= 80 | below 80 |
| --- | --- | --- | --- | --- | --- |
| hosted | diff | 87 | 86 | 48/79 | 9/17 |
| hosted | claim | 88 | 85 | 48/82 | 6/14 |
| hosted | hedge | 85 | 82 | 35/60 | 17/36 |

## Verdict by diff size (all arms)

- hosted, small (<= median): judged PASS 88/144, correct 80/144 (truly passing 60).
- hosted, large: judged PASS 77/144, correct 83/144 (truly passing 84).

## Stability

Repeated hosted judgements (arm diff): 19/24 gave the same verdict as the first time.

## Time, tokens and cost

| model | judgements | median s | total h | mean input | mean cached | mean output | $ at list prices | tool calls attempted |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hosted | 288 | 9 | 0.74 | 12.8k | 10.2k | 0.55k | 0.40 | 0 |
