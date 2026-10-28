# okf-local: analysis

60 runs from `results/main`. A pass means the run finished and its hidden test passed.

## Passes by arm and task (higher is better)

| Task | `no_okf` local | `okf` local | `source` local | `no_okf` hosted | `okf` hosted | `source` hosted |
| --- | --- | --- | --- | --- | --- | --- |
| g1_delete_item | 4/5 | 5/5 | 5/5 | 3/5 | 5/5 | 5/5 |
| g2_add_voucher | 0/5 | 5/5 | 5/5 | 0/5 | 5/5 | 4/5 |
| g3_checkout_request | 0/5 | 5/5 | 4/5 | 0/5 | 3/5 | 4/5 |
| g4_orders_list | 0/5 | 5/5 | 5/5 | 0/5 | 5/5 | 5/5 |
| **Total** | **4/20** | **20/20** | **19/20** | **3/20** | **18/20** | **18/20** |

## Hypotheses (one-sided, Holm-adjusted together)

Effect: the mean over tasks of the difference in pass rate (points), or in mean wall time (seconds; negative means `okf` is faster).

| # | Hypothesis | Effect (95% interval) | p | Holm p | Verdict |
| --- | --- | --- | --- | --- | --- |
| H1 | `okf` passes more than `no_okf` | +80.0 points (+75.0 points to +90.0 points) | 0.0000 | 0.0000 | confirmed |
| H2 | `okf` passes more than `source` | +5.0 points (+0.0 points to +15.0 points) | 0.4988 | 0.9976 | no measurable difference |
| H3 | `okf` runs take less wall time than `source` | +60 s (-60 to +188) | 0.8018 | 0.9976 | no measurable difference |

## Did the arms happen as designed?

- `okf`: 20 of 20 runs opened the guide.
- `source`: 20 of 20 runs read the backend.
- Runs that reached outside what their arm allows: 0.

## Secondary (not tested)

- `source` against `no_okf`, passes: +75.0 points.

| Arm | Runs | Timeouts | Correct but timed out | Median wall time (lower is better) | Median tokens (lower is better) | Median turns | Mean energy per run, Wh (lower is better) | Energy cost per run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `no_okf` | 20 | 1 | 0 | 7.4 min | 308k | 14 | 11.5 | £0.003 |
| `okf` | 20 | 0 | 0 | 4.3 min | 260k | 16 | 8.4 | £0.002 |
| `source` | 20 | 0 | 0 | 4.0 min | 251k | 19 | 7.0 | £0.002 |

Hosted test G for comparison: median time per run 38 to 45 s; tokens per run 294k (`no_okf`), 301k (`okf`), 333k (`source`).
