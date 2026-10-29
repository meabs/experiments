# Analysis of main

720 agent calls; 60 complete case-repeats. Calls without a valid assessment: 0. Non-zero exit codes: 0.

## Correct decisions, one false fact (the 21 observable scenarios)

Correct decisions out of case-repeats (higher is better). Confident wrong: wrong, uncertainty "low" and no suspected manipulation (for B and C: all three members; lower is better). Mean cost per case-repeat at list prices, including every call the arm needs (lower is better).

| Arm | Correct (higher is better) | Confident wrong (lower is better) | Mean tokens | Mean cost, $ (lower is better) |
| --- | --- | --- | --- | --- |
| A. One Luna agent | 17/42 | 9/42 | 43,126 | 0.0031 |
| B. Three Luna agents, independent vote | 20/42 | 7/42 | 129,354 | 0.0094 |
| C. Three Luna agents after peer review | 13/42 | 7/42 | 258,020 | 0.0188 |
| E. One Luna agent, token-matched (4 passes) | 20/42 | 10/42 | 332,837 | 0.0247 |
| F. Sol reviews the team (C) | 19/42 | 13/42 | 315,236 | 0.0875 |
| G. Sol alone | 19/42 | 7/42 | 61,922 | 0.0701 |

## Correct decisions, clean evidence (9 scenarios)

Correct decisions out of case-repeats (higher is better). Confident wrong: wrong, uncertainty "low" and no suspected manipulation (for B and C: all three members; lower is better). Mean cost per case-repeat at list prices, including every call the arm needs (lower is better).

| Arm | Correct (higher is better) | Confident wrong (lower is better) | Mean tokens | Mean cost, $ (lower is better) |
| --- | --- | --- | --- | --- |
| A. One Luna agent | 18/18 | 0/18 | 41,395 | 0.0026 |
| B. Three Luna agents, independent vote | 18/18 | 0/18 | 125,862 | 0.0081 |
| C. Three Luna agents after peer review | 17/18 | 0/18 | 256,816 | 0.0174 |
| E. One Luna agent, token-matched (4 passes) | 18/18 | 0/18 | 311,188 | 0.0224 |
| F. Sol reviews the team (C) | 16/18 | 0/18 | 309,601 | 0.0759 |
| G. Sol alone | 18/18 | 0/18 | 51,875 | 0.0574 |

## Correlated errors and herding (falsified cases)

- Independent agents (B): single-agent error rate 0.52. All three wrong in 18/42 triples; if errors were independent, expected 6.0.
- After peer review (C): all three wrong in 26/42 triples.
- Member answers after peer review: right to wrong 23, wrong to right 4, unchanged right 37, unchanged wrong 62.
- Sol overruled the team in 6/42; right when overruling: 6; Sol agreed with a wrong team: 23.
- Token-matched agent (E): first pass right 22/42, after four passes 20/42.

## Hypotheses (falsified cases; unit = case)

Per case: correct repeats in one arm minus the other. Positive means the first arm got more right.

| # | comparison | cases + / 0 / − | mean difference per case-repeat (95% CI) | Holm p |
| --- | --- | --- | --- | --- |
| H1 | B − A: an independent vote of three vs one agent | 3 / 18 / 0 | +0.07 (+0.00 to +0.14) | 0.5 |
| H2 | C − B: all three wrong, after peer review vs independent (one-sided, more) | 6 / 14 / 1 | +0.19 (+0.00 to +0.40) | 0.312 |
| H3 | C − E: peer review vs one token-matched agent | 0 / 16 / 5 | -0.17 (-0.31 to -0.05) | 0.312 |
| H4 | F − C: Sol's final review vs the team without it | 4 / 17 / 0 | +0.14 (+0.02 to +0.29) | 0.375 |
| H5 | F − G: Sol shown the team's answers vs Sol alone | 3 / 15 / 3 | +0.00 (-0.12 to +0.12) | 1 |

## Cost

| Model | Stage | Calls | Total $ at list price | Median seconds per call |
| --- | --- | --- | --- | --- |
| gpt-5.6-luna | recheck | 240 | 1.44 | 11 |
| gpt-5.6-luna | revise | 180 | 0.56 | 17 |
| gpt-5.6-luna | solo | 180 | 0.54 | 17 |
| gpt-5.6-sol | sol_review | 60 | 3.94 | 23 |
| gpt-5.6-sol | sol_solo | 60 | 3.98 | 22 |

Total: $10.46.
