# Analysis of pilot

48 agent calls; 4 complete case-repeats. Calls without a valid assessment: 0. Non-zero exit codes: 0.

## Correct decisions, one false fact (the 21 observable scenarios)

Correct decisions out of case-repeats (higher is better). Confident wrong: wrong, uncertainty "low" and no suspected manipulation (for B and C: all three members; lower is better). Mean cost per case-repeat at list prices, including every call the arm needs (lower is better).

| Arm | Correct (higher is better) | Confident wrong (lower is better) | Mean tokens | Mean cost, $ (lower is better) |
| --- | --- | --- | --- | --- |
| A. One Luna agent | 1/3 | 2/3 | 41,947 | 0.0036 |
| B. Three Luna agents, independent vote | 1/3 | 1/3 | 125,684 | 0.0114 |
| C. Three Luna agents after peer review | 1/3 | 1/3 | 260,753 | 0.0236 |
| E. One Luna agent, token-matched (4 passes) | 0/3 | 0/3 | 279,170 | 0.0243 |
| F. Sol reviews the team (C) | 1/3 | 2/3 | 314,925 | 0.1045 |
| G. Sol alone | 0/3 | 2/3 | 63,556 | 0.0721 |

## Correct decisions, clean evidence (9 scenarios)

Correct decisions out of case-repeats (higher is better). Confident wrong: wrong, uncertainty "low" and no suspected manipulation (for B and C: all three members; lower is better). Mean cost per case-repeat at list prices, including every call the arm needs (lower is better).

| Arm | Correct (higher is better) | Confident wrong (lower is better) | Mean tokens | Mean cost, $ (lower is better) |
| --- | --- | --- | --- | --- |
| A. One Luna agent | 1/1 | 0/1 | 41,817 | 0.0040 |
| B. Three Luna agents, independent vote | 1/1 | 0/1 | 124,754 | 0.0118 |
| C. Three Luna agents after peer review | 1/1 | 0/1 | 253,501 | 0.0225 |
| E. One Luna agent, token-matched (4 passes) | 1/1 | 0/1 | 346,780 | 0.0274 |
| F. Sol reviews the team (C) | 1/1 | 0/1 | 289,719 | 0.0984 |
| G. Sol alone | 1/1 | 0/1 | 58,741 | 0.0847 |

## Correlated errors and herding (falsified cases)

- Independent agents (B): single-agent error rate 0.67. All three wrong in 2/3 triples; if errors were independent, expected 0.9.
- After peer review (C): all three wrong in 2/3 triples.
- Member answers after peer review: right to wrong 0, wrong to right 0, unchanged right 3, unchanged wrong 6.
- Sol overruled the team in 0/3; right when overruling: 0; Sol agreed with a wrong team: 2.
- Token-matched agent (E): first pass right 0/3, after four passes 0/3.

## Hypotheses (falsified cases; unit = case)

Per case: correct repeats in one arm minus the other. Positive means the first arm got more right.

| # | comparison | cases + / 0 / − | mean difference per case-repeat (95% CI) | Holm p |
| --- | --- | --- | --- | --- |
| H1 | B − A: an independent vote of three vs one agent | 0 / 3 / 0 | +0.00 (+0.00 to +0.00) | 1 |
| H2 | C − B: all three wrong, after peer review vs independent (one-sided, more) | 0 / 3 / 0 | +0.00 (+0.00 to +0.00) | 1 |
| H3 | C − E: peer review vs one token-matched agent | 1 / 2 / 0 | +0.33 (+0.00 to +1.00) | 1 |
| H4 | F − C: Sol's final review vs the team without it | 0 / 3 / 0 | +0.00 (+0.00 to +0.00) | 1 |
| H5 | F − G: Sol shown the team's answers vs Sol alone | 1 / 2 / 0 | +0.33 (+0.00 to +1.00) | 1 |

## Cost

| Model | Stage | Calls | Total $ at list price | Median seconds per call |
| --- | --- | --- | --- | --- |
| gpt-5.6-luna | recheck | 16 | 0.10 | 10 |
| gpt-5.6-luna | revise | 12 | 0.05 | 19 |
| gpt-5.6-luna | solo | 12 | 0.05 | 17 |
| gpt-5.6-sol | sol_review | 4 | 0.32 | 23 |
| gpt-5.6-sol | sol_solo | 4 | 0.30 | 21 |

Total: $0.81.
