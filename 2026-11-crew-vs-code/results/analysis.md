# crew-vs-code: analysis

6080 runs from `main`. Crashed: 0. Transport retries (OpenRouter): 1. Judged: 6080.

## Resolved, by level

Share of runs resolved (right state changes and every required fact in the reply); **higher is better**. Both wordings and both account sizes pooled; Wilson 95% interval for the total.

| Architecture | 1 simple | 2 multi-step | 3 branching | 4 recovery | 5 other requests | 6 compound | All |
| --- | --- | --- | --- | --- | --- | --- | --- |
| State machine, Luna | 100% | 100% | 92% | 67% | 100% | 100% | **93% (91–95)** |
| Single agent, Luna | 100% | 100% | 99% | 78% | 100% | 96% | **96% (94–97)** |
| Crew, shared history, Luna | 100% | 100% | 81% | 65% | 77% | 62% | **81% (78–83)** |
| Crew, note only, Luna | 100% | 99% | 99% | 71% | 88% | 86% | **91% (89–93)** |
| State machine, Qwen | 100% | 100% | 89% | 67% | 99% | 94% | **91% (89–93)** |
| Single agent, Qwen | 100% | 98% | 88% | 71% | 98% | 80% | **89% (87–91)** |
| Crew, shared history, Qwen | 100% | 68% | 79% | 47% | 82% | 39% | **70% (67–73)** |
| Crew, note only, Qwen | 99% | 75% | 86% | 49% | 80% | 58% | **75% (72–78)** |

## How runs ended

Share of all runs. Resolved: **higher is better**. Escalated (handed to a person when not required), wrong (missed action or missing information) and harmful (a refund, replacement, cancellation or address change the policy didn't call for): **lower is better**.

| Architecture | Resolved | Escalated | Wrong | Harmful | Harmful runs (count) |
| --- | --- | --- | --- | --- | --- |
| State machine, Luna | 93% | 5% | 2% | 0% | 0 |
| Single agent, Luna | 96% | 2% | 2% | 0% | 2 |
| Crew, shared history, Luna | 81% | 4% | 15% | 0% | 0 |
| Crew, note only, Luna | 91% | 3% | 6% | 0% | 2 |
| State machine, Qwen | 91% | 5% | 3% | 0% | 0 |
| Single agent, Qwen | 89% | 1% | 7% | 4% | 27 |
| Crew, shared history, Qwen | 70% | 2% | 25% | 3% | 24 |
| Crew, note only, Qwen | 75% | 2% | 21% | 2% | 16 |

## False action claims

Share of runs whose reply tells the customer an action was taken (refund, replacement, cancellation, address change, handed to a team) that the shop's log shows wasn't; **lower is better**. By level, and the total with its Wilson 95% interval.

| Architecture | 1 simple | 2 multi-step | 3 branching | 4 recovery | 5 other requests | 6 compound | All | Most common claim |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| State machine, Luna | 0% | 0% | 0% | 0% | 0% | 0% | **0% (0–1)** | – |
| Single agent, Luna | 0% | 0% | 0% | 0% | 0% | 0% | **0% (0–1)** | – |
| Crew, shared history, Luna | 0% | 0% | 14% | 1% | 18% | 29% | **11% (9–13)** | handed_to_team (80) |
| Crew, note only, Luna | 0% | 1% | 0% | 0% | 13% | 1% | **2% (2–4)** | handed_to_team (18) |
| State machine, Qwen | 0% | 0% | 0% | 0% | 0% | 0% | **0% (0–1)** | – |
| Single agent, Qwen | 0% | 1% | 1% | 1% | 1% | 4% | **1% (1–2)** | handed_to_team (6) |
| Crew, shared history, Qwen | 0% | 25% | 10% | 22% | 14% | 35% | **17% (15–20)** | handed_to_team (66) |
| Crew, note only, Qwen | 0% | 22% | 5% | 22% | 13% | 20% | **13% (11–16)** | refund (68) |

## Crew handoffs

Handoffs per run (mean), and the share of runs on cases that need an action where the front desk replied without handing over (it can't act itself; **lower is better**).

| Crew | Handoffs per run | Front desk replied alone, action needed |
| --- | --- | --- |
| Crew, shared history, Luna | 0.83 | 6% (4–8) |
| Crew, note only, Luna | 0.87 | 6% (4–8) |
| Crew, shared history, Qwen | 0.71 | 20% (17–23) |
| Crew, note only, Qwen | 0.70 | 23% (19–26) |

## Cost, calls, time and consistency

Mean cost per run (OpenRouter's billed cost) and per resolved run, mean model calls, median wall time; **lower is better**. Consistency: share of case × wording × account conditions where all repetitions ended the same way; **higher is better**.

| Architecture | Cost per run | Cost per resolved run | Model calls | Median seconds | Consistency | Total cost |
| --- | --- | --- | --- | --- | --- | --- |
| State machine, Luna | $0.00018 | $0.00019 | 2.0 | 4.5 | 99% | $0.14 |
| Single agent, Luna | $0.00023 | $0.00024 | 3.9 | 7.9 | 90% | $0.17 |
| Crew, shared history, Luna | $0.00049 | $0.00061 | 4.5 | 10.0 | 69% | $0.37 |
| Crew, note only, Luna | $0.00048 | $0.00053 | 5.7 | 10.5 | 84% | $0.36 |
| State machine, Qwen | $0.00043 | $0.00047 | 2.0 | 28.5 | 93% | $0.32 |
| Single agent, Qwen | $0.00022 | $0.00025 | 4.0 | 11.8 | 82% | $0.17 |
| Crew, shared history, Qwen | $0.00042 | $0.00060 | 4.5 | 18.4 | 42% | $0.32 |
| Crew, note only, Qwen | $0.00046 | $0.00061 | 5.4 | 22.3 | 53% | $0.35 |

Total: $2.20 for 6080 runs.

## Hypotheses

Difference in resolved rate (first arm minus second, percentage points); permutation p within case × wording × account size (10,000, seed 1); Holm over H1–H3 within each model.

| Model | Hypothesis | Levels | Difference | p | Holm p |
| --- | --- | --- | --- | --- | --- |
| Luna | H1: state machine > crew (shared) | 1,2,3 | +4.7 | 0.0004 | 0.0008 |
| Luna | H2: crew (shared) > single agent | 6 | -34.2 | 1.0000 | 1.0000 |
| Luna | H3: crew (shared) ≠ crew (note) | 1,2,3,4,5,6 | -10.3 | 0.0001 | 0.0003 |
| Qwen | H1: state machine > crew (shared) | 1,2,3 | +13.2 | 0.0001 | 0.0003 |
| Qwen | H2: crew (shared) > single agent | 6 | -40.8 | 1.0000 | 1.0000 |
| Qwen | H3: crew (shared) ≠ crew (note) | 1,2,3,4,5,6 | -5.1 | 0.0071 | 0.0142 |
