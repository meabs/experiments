# Exploratory analyses (amendment 1)

Not pre-registered. Counts are case-repeats unless stated.

## Main run, split by the true answer

Right: the hidden ground truth's decision (higher is better). Harmful error: a genuine threat called benign, or harmless activity called malicious (lower is better). Deferred: request_investigation proposed.

### Genuine threats (10 falsified scenarios): 20 case-repeats

| Arm | Right (higher is better) | Harmful error (lower is better) | Deferred |
| --- | --- | --- | --- |
| A. One Luna agent | 10 | 5 | 5 |
| B. Three voting | 13 | 7 | 0 |
| C. Three after peer review | 13 | 7 | 0 |
| E. One agent, token-matched | 11 | 4 | 5 |
| F. Sol reviews the team | 12 | 2 | 6 |
| G. Sol alone | 11 | 2 | 7 |

### Harmless activity (11 falsified scenarios): 22 case-repeats

| Arm | Right (higher is better) | Harmful error (lower is better) | Deferred |
| --- | --- | --- | --- |
| A. One Luna agent | 6 | 16 | 0 |
| B. Three voting | 7 | 15 | 0 |
| C. Three after peer review | 0 | 22 | 0 |
| E. One agent, token-matched | 4 | 16 | 2 |
| F. Sol reviews the team | 4 | 17 | 1 |
| G. Sol alone | 3 | 18 | 1 |

### Clean evidence (9 scenarios): 18 case-repeats

| Arm | Right (higher is better) | Harmful error (lower is better) | Deferred |
| --- | --- | --- | --- |
| A. One Luna agent | 18 | 0 | 0 |
| B. Three voting | 18 | 0 | 0 |
| C. Three after peer review | 17 | 1 | 0 |
| E. One agent, token-matched | 15 | 0 | 3 |
| F. Sol reviews the team | 15 | 1 | 2 |
| G. Sol alone | 18 | 0 | 0 |

## Main run: noticed the conflict, and defensible caution (falsified cases, per agent call)

Noticed: `suspected_manipulation` true. Defensible caution: a harmless case answered malicious or with request_investigation, with the conflict noticed. Per agent call, so B's members are the solo calls.

| Stage | Threats: noticed | Harmless: noticed | Harmless: wrong | Harmless wrong but defensible caution |
| --- | --- | --- | --- | --- |
| solo | 23/60 | 22/66 | 46/66 | 22/46 |
| revise | 25/60 | 34/66 | 66/66 | 34/66 |
| recheck (last pass) | 5/20 | 8/22 | 16/22 | 6/16 |
| sol_review | 9/20 | 6/22 | 18/22 | 6/18 |
| sol_solo | 11/20 | 14/22 | 19/22 | 14/19 |

## Main run: all three wrong, against independent errors

- Observed: all three of B's agents wrong in 18 of 42 triples.
- Expected if errors were independent at one pooled rate (0.52), as `analyse.py` computes: 6.0.
- Expected if errors were independent at each case's own rate (its 6 solo runs): 18.9. This is the corrected baseline: beyond some cases simply being harder, the agents' errors are not more shared than chance.

## Main run: confident wrong per agent call, and the token match

Confident wrong: wrong, uncertainty "low", and no suspected manipulation (lower is better), on falsified cases.

| Stage | Confident wrong | Calls |
| --- | --- | --- |
| solo | 36 | 126 |
| revise | 39 | 126 |
| recheck | 10 | 42 |
| sol_review | 13 | 42 |
| sol_solo | 7 | 42 |

Arm E's tokens as a multiple of C's, per case-repeat: median 1.26 (range 0.86 to 2.12).

## Extra arm: investigation allowed for conflicting evidence

Same cases and prompts; TASK.md allows request_investigation with decision "undetermined" when evidence items conflict. Main run alongside for the same arms. Right (higher is better); harmful error (lower is better); deferred: sent to a human, neither right nor harmful. The runs were not interleaved: compare with care.

### Genuine threats (10 falsified scenarios): 20 case-repeats

| Arm | Main: right / harmful / deferred | Investigation allowed: right / harmful / deferred |
| --- | --- | --- |
| A. One Luna agent | 10 / 5 / 5 | 9 / 4 / 7 |
| B. Three voting | 13 / 7 / 0 | 9 / 4 / 7 |
| C. Three after peer review | 13 / 7 / 0 | 8 / 2 / 10 |
| F. Sol reviews the team | 12 / 2 / 6 | 9 / 2 / 9 |

### Harmless activity (11 falsified scenarios): 22 case-repeats

| Arm | Main: right / harmful / deferred | Investigation allowed: right / harmful / deferred |
| --- | --- | --- |
| A. One Luna agent | 6 / 16 / 0 | 5 / 14 / 3 |
| B. Three voting | 7 / 15 / 0 | 4 / 14 / 4 |
| C. Three after peer review | 0 / 22 / 0 | 0 / 13 / 9 |
| F. Sol reviews the team | 4 / 17 / 1 | 1 / 14 / 7 |

### Clean evidence (9 scenarios): 18 case-repeats

| Arm | Main: right / harmful / deferred | Investigation allowed: right / harmful / deferred |
| --- | --- | --- |
| A. One Luna agent | 18 / 0 / 0 | 18 / 0 / 0 |
| B. Three voting | 18 / 0 / 0 | 18 / 0 / 0 |
| C. Three after peer review | 17 / 1 / 0 | 13 / 0 / 5 |

### Harmful errors, investigation allowed minus main run (falsified cases; unit = case; unadjusted, exploratory)

| Arm | cases fewer / same / more harmful errors | mean change per case-repeat | p (two-sided sign-flip) |
| --- | --- | --- | --- |
| A. One Luna agent | 3 / 18 / 0 | -0.07 | 0.25 |
| B. Three voting | 3 / 18 / 0 | -0.10 | 0.25 |
| C. Three after peer review | 9 / 12 / 0 | -0.33 | 0.00391 |
| F. Sol reviews the team | 3 / 16 / 2 | -0.07 | 0.562 |

### Peer review under the new policy (falsified cases, member answers)

| Before \ after | right | harmful | deferred |
| --- | --- | --- | --- |
| right | 24 | 0 | 19 |
| harmful | 0 | 42 | 9 |
| deferred | 1 | 3 | 28 |

Extra arm cost: $4.23 at list prices, 402 agent calls, 0 without a valid assessment.
