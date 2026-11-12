# FUT-1 cross-pair results (cropped re-score, exploratory)

100 judge calls, judges: anthropic/claude-sonnet-5.5, google/gemini-4-argon.

Mean pair score = share of votes for the factory design over the 25 plain x factory pairs (0.5 = no preference; above 0.5 favours the factory, below 0.5 the plain agent). Obs = factory minus plain mean win share (= 2 x score - 1). p: permutation over the 252 splits of the 10 runs (approximate); interval: bootstrap over runs.

| Criterion | Mean pair score (95% interval) | Obs | p | Pairs factory wins | plain wins | split | claude-sonnet-5.5 | gemini-4-argon |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| overall | 0.01 (0.00 to 0.06) | -0.98 | 0.008 | 0 | 25 | 0 | 0.00 | 0.02 |
| novelty | 0.00 (0.00 to 0.00) | -1.00 | 0.008 | 0 | 25 | 0 | 0.00 | 0.00 |
| fit | 0.00 (0.00 to 0.00) | -1.00 | 0.008 | 0 | 25 | 0 | 0.00 | 0.00 |
| plausible | 0.73 (0.63 to 0.81) | +0.47 | 0.008 | 22 | 1 | 2 | 0.98 | 0.49 |
| hierarchy | 0.32 (0.14 to 0.49) | -0.36 | 0.008 | 4 | 14 | 7 | 0.32 | 0.32 |
| polish | 0.38 (0.17 to 0.60) | -0.24 | 0.119 | 5 | 12 | 8 | 0.48 | 0.28 |
| identity | 0.00 (0.00 to 0.00) | -1.00 | 0.008 | 0 | 25 | 0 | 0.00 | 0.00 |

Judge position bias (share choosing the design shown first on 'overall'; same choice in both orders):

- anthropic/claude-sonnet-5.5: first-shown 50%, same choice in both orders 100%
- google/gemini-4-argon: first-shown 52%, same choice in both orders 96%
