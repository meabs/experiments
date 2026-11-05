# okf-stale analysis: main

144 runs.

## Outcome on the stale fact

Runs per arm and ticket: truth / stale / other (the change followed the code or contract / the stale statement / neither). For truth higher is better, for stale lower is better.

| Arm | F7 (S1 template name) | F6 (S2 timeout and reference) | F3 (S3 rejected payments and the limit) | All |
| --- | --- | --- | --- | --- |
| A, correct | 8 / 0 / 0 (of 8) | 6 / 0 / 2 (of 8) | 8 / 0 / 0 (of 8) | 22 / 0 / 2 (of 24) |
| B, stale | 8 / 0 / 0 (of 8) | 0 / 8 / 0 (of 8) | 8 / 0 / 0 (of 8) | 16 / 8 / 0 (of 24) |
| D, stale + metadata | 8 / 0 / 0 (of 8) | 0 / 8 / 0 (of 8) | 8 / 0 / 0 (of 8) | 16 / 8 / 0 (of 24) |
| E, stale + instruction | 8 / 0 / 0 (of 8) | 6 / 0 / 2 (of 8) | 8 / 0 / 0 (of 8) | 22 / 0 / 2 (of 24) |
| F, correct + instruction | 8 / 0 / 0 (of 8) | 8 / 0 / 0 (of 8) | 8 / 0 / 0 (of 8) | 24 / 0 / 0 (of 24) |
| V, no bundle | 8 / 0 / 0 (of 8) | 2 / 0 / 6 (of 8) | 8 / 0 / 0 (of 8) | 18 / 0 / 6 (of 24) |

Fully correct (every hidden and existing test; higher is better):

| Arm | F7 | F6 | F3 | All |
| --- | --- | --- | --- | --- |
| A, correct | 8/8 | 6/8 | 8/8 | 22/24 |
| B, stale | 8/8 | 0/8 | 8/8 | 16/24 |
| D, stale + metadata | 7/8 | 0/8 | 8/8 | 15/24 |
| E, stale + instruction | 8/8 | 6/8 | 8/8 | 22/24 |
| F, correct + instruction | 8/8 | 8/8 | 8/8 | 24/24 |
| V, no bundle | 8/8 | 2/8 | 8/8 | 18/24 |

## Hypotheses

Differences are in percentage points, the first arm minus the second, averaged over the three tickets. One-sided permutation p, Holm-adjusted across H1 and H3 to H6.

| # | Statement | Difference | 95% interval | p | Holm p |
| --- | --- | --- | --- | --- | --- |
| H1 | E follows the stale fact less often than B (B − E) | +33 | +33 to +33 | 0.0002 | 0.0008 |
| H3 | B ends wrong (stale or other) more often than A (B − A) | +25 | +12 to +33 | 0.0046 | 0.0138 |
| H4 | B is fully correct less often than V (V − B) | +8 | +0 to +21 | 0.2346 | 0.4692 |
| H5 | D follows the stale fact less often than B (B − D) | +0 | +0 to +0 | 1.0000 | 1.0000 |
| H6 | E reports the conflict more often than B (E − B) | +54 | +33 to +75 | 0.0001 | 0.0005 |

**H2** (E rarely follows it): E followed the stale fact in 0 of 24 runs (0%); 95% Clopper-Pearson interval 0% to 14%; supported if the upper end is below 25%: **yes**.

## How the runs decided (from the transcripts)

Share of runs (higher means more checking):

| Arm | Opened okf/ | Opened the ticket's source of truth | ...before the first edit | Opened contracts/ | Ran `date` | Mentioned freshness | Conflict reported (judge) | Asked the user |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A, correct | 100% | 62% | 62% | 33% | 0% | 29% | 0% | 0% |
| B, stale | 100% | 46% | 46% | 33% | 0% | 25% | 0% | 0% |
| D, stale + metadata | 100% | 58% | 58% | 33% | 0% | 17% | 0% | 0% |
| E, stale + instruction | 100% | 100% | 100% | 96% | 0% | 46% | 54% | 0% |
| F, correct + instruction | 100% | 96% | 96% | 96% | 0% | 17% | 0% | 0% |
| V, no bundle | 0% | 46% | 46% | 33% | 0% | 25% | 0% | 0% |

Outcome by whether the run opened the ticket's source of truth before its first edit (runs following the stale fact / runs):

| Arm | Opened it first | Didn't |
| --- | --- | --- |
| A, correct | 0/15 | 0/9 |
| B, stale | 0/11 | 8/13 |
| D, stale + metadata | 0/14 | 8/10 |
| E, stale + instruction | 0/24 | 0/0 |
| F, correct + instruction | 0/23 | 0/1 |
| V, no bundle | 0/11 | 0/13 |

## Exploratory: the instruction's cost on a correct bundle (F against A)

- fully correct: F − A +8 points (one-sided p for F > A 0.237)
- truth: F − A +8 points (one-sided p for F > A 0.237)

## Tokens, time and cost

Mean per run: input (of which new, not cached) / output tokens; seconds; list-price cost (lower is cheaper).

| Arm | F7 | F6 | F3 | Seconds | Cost per run | Cost per fully correct run |
| --- | --- | --- | --- | --- | --- | --- |
| A, correct | 255k (32k new) / 3.2k | 298k (42k new) / 4.2k | 307k (35k new) / 3.6k | 90 | $0.017 | $0.018 |
| B, stale | 242k (32k new) / 3.0k | 723k (55k new) / 6.6k | 339k (43k new) / 3.6k | 109 | $0.022 | $0.033 |
| D, stale + metadata | 242k (38k new) / 3.3k | 437k (44k new) / 5.2k | 325k (42k new) / 3.5k | 97 | $0.019 | $0.030 |
| E, stale + instruction | 317k (40k new) / 3.9k | 546k (54k new) / 5.5k | 270k (35k new) / 3.5k | 104 | $0.020 | $0.022 |
| F, correct + instruction | 315k (37k new) / 3.7k | 442k (41k new) / 5.0k | 291k (40k new) / 3.6k | 100 | $0.019 | $0.019 |
| V, no bundle | 218k (31k new) / 3.0k | 282k (34k new) / 4.2k | 250k (35k new) / 3.4k | 86 | $0.015 | $0.020 |

## Robustness

- Second judge (`anthropic/claude-sonnet-5.5`) on conflict reported: agrees on 144 of 144 runs.
- H6 under the second judge: E − B +54 points, one-sided p 0.0001.
- H1 with *other* counted as stale: B − E +25 points, one-sided p 0.0043.
