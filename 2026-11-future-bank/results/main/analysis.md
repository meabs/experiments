# FUT-1 cross-pair results (uncropped captures, primary)

100 judge calls, judges: anthropic/claude-sonnet-5.5, google/gemini-4-argon.

Mean pair score = share of votes for the factory design over the 25 plain x factory pairs (0.5 = no preference; above 0.5 favours the factory, below 0.5 the plain agent). Obs = factory minus plain mean win share (= 2 x score - 1). p: permutation over the 252 splits of the 10 runs (approximate); interval: bootstrap over runs.

| Criterion | Mean pair score (95% interval) | Obs | p | Pairs factory wins | plain wins | split | claude-sonnet-5.5 | gemini-4-argon |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| overall | 0.03 (0.00 to 0.10) | -0.94 | 0.008 | 0 | 25 | 0 | 0.00 | 0.06 |
| novelty | 0.00 (0.00 to 0.00) | -1.00 | 0.008 | 0 | 25 | 0 | 0.00 | 0.00 |
| fit | 0.00 (0.00 to 0.00) | -1.00 | 0.008 | 0 | 25 | 0 | 0.00 | 0.00 |
| plausible | 0.61 (0.30 to 0.85) | +0.22 | 0.222 | 16 | 5 | 4 | 0.79 | 0.43 |
| hierarchy | 0.29 (0.07 to 0.60) | -0.41 | 0.032 | 4 | 16 | 5 | 0.32 | 0.27 |
| polish | 0.41 (0.13 to 0.72) | -0.18 | 0.349 | 8 | 14 | 3 | 0.42 | 0.40 |
| identity | 0.00 (0.00 to 0.00) | -1.00 | 0.008 | 0 | 25 | 0 | 0.00 | 0.00 |

Judge position bias (share choosing the design shown first on 'overall'; same choice in both orders):

- anthropic/claude-sonnet-5.5: first-shown 50%, same choice in both orders 100%
- google/gemini-4-argon: first-shown 56%, same choice in both orders 88%
