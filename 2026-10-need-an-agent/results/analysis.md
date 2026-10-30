# Do you actually need an agent? Analysis

4480 runs from `main`. Crashed: 0. Transport retries (OpenRouter): 3.

## Resolved, by level

Share of runs resolved (right actions and a reply with the required facts); **higher is better**. Both wordings and both account sizes pooled.

| Architecture | 1 simple | 2 multi-step | 3 branching | 4 recovery | 5 unanticipated | All |
| --- | --- | --- | --- | --- | --- | --- |
| Plain code | 92% | 92% | 88% | 42% | 17% | **67% (63–71)** |
| One call, Luna | 100% | 100% | 100% | 48% | 100% | **90% (88–92)** |
| One call, Qwen | 100% | 99% | 83% | 50% | 78% | **82% (79–85)** |
| Workflow, Luna | 100% | 100% | 92% | 42% | 17% | **71% (68–75)** |
| Workflow, Qwen | 99% | 100% | 92% | 44% | 12% | **71% (67–74)** |
| Agent, Luna | 100% | 100% | 99% | 74% | 98% | **95% (92–96)** |
| Agent, Qwen | 100% | 98% | 92% | 67% | 98% | **91% (89–93)** |

## Resolved, by wording

Share resolved; **higher is better**.

| Architecture | original | paraphrased |
| --- | --- | --- |
| Plain code | 72% (67–77) | 62% (57–68) |
| One call, Luna | 90% (86–93) | 91% (87–93) |
| One call, Qwen | 83% (78–87) | 81% (77–85) |
| Workflow, Luna | 71% (66–76) | 72% (66–76) |
| Workflow, Qwen | 70% (64–74) | 72% (67–77) |
| Agent, Luna | 95% (92–97) | 94% (91–96) |
| Agent, Qwen | 92% (89–95) | 90% (86–93) |

## Resolved, by account size

Share resolved; **higher is better**.

| Architecture | small | large |
| --- | --- | --- |
| Plain code | 70% (65–75) | 64% (59–69) |
| One call, Luna | 91% (87–93) | 90% (86–93) |
| One call, Qwen | 81% (76–85) | 83% (79–87) |
| Workflow, Luna | 75% (70–79) | 68% (63–73) |
| Workflow, Qwen | 74% (69–79) | 68% (63–73) |
| Agent, Luna | 94% (91–96) | 95% (92–97) |
| Agent, Qwen | 92% (88–94) | 91% (87–94) |

## How runs ended

Share of all runs. Resolved: **higher is better**. Escalated: handed to a human when the policy didn't require it (safe, but a person has to do it). Wrong: missed action or missing information. Harmful: a refund, replacement, cancellation or address change the policy didn't call for. **Lower is better** for the last three.

| Architecture | Resolved | Escalated | Wrong | Harmful | Harmful runs (count) |
| --- | --- | --- | --- | --- | --- |
| Plain code | 67% | 19% | 11% | 3% | 20 |
| One call, Luna | 90% | 7% | 3% | 0% | 0 |
| One call, Qwen | 82% | 12% | 3% | 3% | 20 |
| Workflow, Luna | 71% | 16% | 12% | 1% | 7 |
| Workflow, Qwen | 71% | 18% | 11% | 1% | 5 |
| Agent, Luna | 95% | 4% | 2% | 0% | 1 |
| Agent, Qwen | 91% | 1% | 5% | 3% | 18 |

## Cost, speed and consistency

Cost at OpenRouter's billed price. **Lower is better** for cost, calls and time; **higher is better** for consistency (conditions where every repetition ended the same way).

| Architecture | Accounts | Cost per 1,000 emails, $ | Cost per resolved email, $ | Median model calls | Median prompt tokens | Median seconds | Consistency |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Plain code | small | 0.00 | 0.00000 | 0 | 0 | 0.0 | 100% |
| Plain code | large | 0.00 | 0.00000 | 0 | 0 | 0.0 | 100% |
| One call, Luna | small | 0.15 | 0.00017 | 1 | 1,362 | 3.2 | 100% |
| One call, Luna | large | 0.45 | 0.00050 | 1 | 11,178 | 3.5 | 98% |
| One call, Qwen | small | 0.24 | 0.00030 | 1 | 1,542 | 15.2 | 88% |
| One call, Qwen | large | 0.52 | 0.00063 | 1 | 13,585 | 16.8 | 89% |
| Workflow, Luna | small | 0.15 | 0.00020 | 2 | 437 | 5.2 | 97% |
| Workflow, Luna | large | 0.15 | 0.00022 | 2 | 427 | 5.2 | 94% |
| Workflow, Qwen | small | 0.36 | 0.00048 | 2 | 476 | 25.5 | 88% |
| Workflow, Qwen | large | 0.35 | 0.00052 | 2 | 463 | 25.8 | 91% |
| Agent, Luna | small | 0.19 | 0.00020 | 4 | 5,100 | 6.8 | 89% |
| Agent, Luna | large | 0.19 | 0.00020 | 4 | 5,580 | 6.5 | 84% |
| Agent, Qwen | small | 0.19 | 0.00020 | 4 | 7,929 | 11.2 | 78% |
| Agent, Qwen | large | 0.19 | 0.00021 | 4 | 8,539 | 11.2 | 91% |

## Per case (resolved runs of all runs)

| Case | Plain code | One call, Luna | One call, Qwen | Workflow, Luna | Workflow, Qwen | Agent, Luna | Agent, Qwen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| L1-01 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 |
| L1-02 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 |
| L1-03 | 10/20 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 |
| L1-04 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 |
| L1-05 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 |
| L1-06 | 20/20 | 20/20 | 20/20 | 20/20 | 19/20 | 20/20 | 20/20 |
| L2-01 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 |
| L2-02 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 | 19/20 |
| L2-03 | 10/20 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 |
| L2-04 | 20/20 | 20/20 | 19/20 | 20/20 | 20/20 | 20/20 | 20/20 |
| L2-05 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 | 19/20 |
| L2-06 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 |
| L3-01 | 20/20 | 20/20 | 19/20 | 20/20 | 20/20 | 20/20 | 20/20 |
| L3-02 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 | 19/20 |
| L3-03 | 20/20 | 20/20 | 10/20 (10 harmful) | 20/20 | 20/20 | 19/20 (1 harmful) | 18/20 (2 harmful) |
| L3-04 | 20/20 | 20/20 | 5/20 | 20/20 | 20/20 | 20/20 | 19/20 |
| L3-05 | 10/20 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 | 19/20 |
| L3-06 | 10/20 | 20/20 | 20/20 | 10/20 | 10/20 | 20/20 | 13/20 |
| L3-07 | 20/20 | 20/20 | 20/20 | 20/20 | 19/20 | 20/20 | 20/20 |
| L3-08 | 20/20 | 20/20 | 19/20 | 17/20 | 18/20 | 19/20 | 20/20 |
| L4-01 | 20/20 | 18/20 | 20/20 | 20/20 | 20/20 | 18/20 | 18/20 |
| L4-02 | 10/20 | 20/20 | 20/20 | 10/20 | 13/20 | 20/20 | 20/20 |
| L4-03 | 0/20 | 0/20 | 0/20 | 0/20 | 0/20 | 5/20 | 4/20 (16 harmful) |
| L4-04 | 0/20 | 0/20 | 0/20 | 0/20 | 0/20 | 15/20 | 18/20 |
| L4-05 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 | 19/20 | 18/20 |
| L4-06 | 0/20 | 0/20 | 0/20 | 0/20 | 0/20 | 12/20 | 2/20 |
| L5-01 | 0/20 | 20/20 | 20/20 | 0/20 | 0/20 | 20/20 | 20/20 |
| L5-02 | 0/20 | 20/20 | 20/20 | 0/20 | 0/20 | 20/20 | 20/20 |
| L5-03 | 0/20 | 20/20 | 20/20 | 0/20 | 0/20 | 20/20 | 19/20 |
| L5-04 | 20/20 | 20/20 | 20/20 | 20/20 | 13/20 (2 harmful) | 18/20 | 20/20 |
| L5-05 | 0/20 | 20/20 | 9/20 (10 harmful) | 0/20 | 2/20 | 20/20 | 20/20 |
| L5-06 | 0/20 (20 harmful) | 20/20 | 4/20 | 0/20 (7 harmful) | 0/20 (3 harmful) | 20/20 | 19/20 |

Total cost: $1.01.
