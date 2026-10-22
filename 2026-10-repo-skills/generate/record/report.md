# Trial report: repo-skills-generate

Baseline arm: **none**. Relative cost is each run's tokens divided by the baseline's mean for the same question; 1.00 means equal, lower is cheaper.

## codex

| arm | runs | correct | tokens per run (95% CI) | relative cost (95% CI) | verdict | turns | used tool | seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| none | 1 | - (verified 1/1) | 3298k | 1.00 | baseline | 30.0 | - | 175 |

## Tokens by question (mean, thousands)

| question | codex/none |
| --- | --- |
| GENERATE | 3298k |

Token totals are not comparable between agents (see adapters.py). Treat a verdict as evidence only when the interval excludes 1.00, and as provisional below 8 runs per arm.

