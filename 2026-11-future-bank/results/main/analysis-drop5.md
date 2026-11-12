# FUT-1 cross-pair results (uncropped captures, primary)

80 judge calls, judges: anthropic/claude-sonnet-5.5, google/gemini-4-argon.

Mean pair score = share of votes for the factory design over the 25 plain x factory pairs (0.5 = no preference; above 0.5 favours the factory, below 0.5 the plain agent). Obs = factory minus plain mean win share (= 2 x score - 1). p: permutation over the 252 splits of the 10 runs (approximate); interval: bootstrap over runs.

| Criterion | Mean pair score (95% interval) | Obs | p | Pairs factory wins | plain wins | split | claude-sonnet-5.5 | gemini-4-argon |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| overall | 0.04 (0.00 to 0.12) | -0.93 | 0.008 | 0 | 20 | 0 | 0.00 | 0.07 |
| novelty | 0.00 (0.00 to 0.00) | -1.00 | 0.008 | 0 | 20 | 0 | 0.00 | 0.00 |
| fit | 0.00 (0.00 to 0.00) | -1.00 | 0.008 | 0 | 20 | 0 | 0.00 | 0.00 |
| plausible | 0.76 (0.63 to 0.89) | +0.52 | 0.008 | 16 | 0 | 4 | 0.99 | 0.54 |
| hierarchy | 0.37 (0.10 to 0.67) | -0.26 | 0.167 | 4 | 11 | 5 | 0.40 | 0.34 |
| polish | 0.49 (0.17 to 0.80) | -0.02 | 0.905 | 8 | 9 | 3 | 0.47 | 0.50 |
| identity | 0.00 (0.00 to 0.00) | -1.00 | 0.008 | 0 | 20 | 0 | 0.00 | 0.00 |

Judge position bias (share choosing the design shown first on 'overall'; same choice in both orders):

- anthropic/claude-sonnet-5.5: first-shown 50%, same choice in both orders 100%
- google/gemini-4-argon: first-shown 57%, same choice in both orders 85%
