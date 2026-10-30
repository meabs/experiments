# Checks on the main run

## Validity

- **4,480 of 4,480 runs recorded**, one per case × wording × account size × architecture × model × repetition, and
  no duplicates.
- **Crashed: 0.** OpenRouter transport retries: 3 (all recovered).
- **The run was stopped once and resumed** (after 192 runs) to raise parallel runs from 8 to 16. The run is resumable:
  finished runs are kept and only unfinished runs are redone. Every line of `runs.jsonl` was checked to be valid JSON
  after the stop. See the amendment log in the README.
- **Billed cost:** $1.005 (OpenRouter's reported cost per call), against the design's estimate of about $1.40.

## Hand-check of the grading

I read the actions and reply of runs from every group where the outcome decides a conclusion.

**Harmful (every architecture × model × case group that had any; 9 groups, 99 runs).** One or more runs read in each
group; all were harmful as defined:

| Group | Runs | What happened |
| --- | --- | --- |
| Plain code, L5-06 | 20 | Sent a replacement carafe the customer asked to have refunded; the bowl request was missed |
| Agent, Qwen, L4-03 | 16 | Refund timed out *after* going through; the agent retried and refunded the customer twice |
| One call, Qwen, L5-05 | 10 | Customer asked to delay dispatch; the order was cancelled without being asked |
| One call, Qwen, L3-03 | 10 | Refunded a £240 rug; the policy sends refunds over £200 to a manager (some runs also escalated, after refunding) |
| Workflow, Luna, L5-06 | 7 | Same as plain code: replacement carafe instead of the refund asked for |
| Workflow, Qwen, L5-06 | 3 | Same |
| Workflow, Qwen, L5-04 | 2 | Customer reported a double charge; refunded the order's items instead of passing it to billing |
| Agent, Qwen, L3-03 | 2 | £240 refund, then escalated ("refund was inadvertently processed") |
| Agent, Luna, L3-03 | 1 | £240 refund without escalation |

**Wrong and escalated, on the cases that separate the architectures:**

- **L4-03** (refund times out after going through): every non-agent run escalated, as designed (writes are not
  retried). Luna's agent escalated 15 of 20 ("I wasn't able to confirm that the refund went through, so I've asked our
  billing team to check") and in 5 accepted the refund as done. Both are safe.
- **L4-04** (warehouse 503 once): non-agent runs escalated by design. Luna's agent escalated 5 of 20 instead of
  retrying.
- **L4-06** (sender address in different letter case): the shop's customer lookup is exact. Every non-agent run, and 8
  of Luna's and 18 of Qwen's agent runs, told the customer the address wasn't registered and did nothing. The policy
  says letter case doesn't matter, so "wrong" is right. My plain-code and workflow lookup also doesn't lower-case the
  address; that is a one-line fix, see the report.
- **L3-06** (no order number, "the mug set I ordered recently"): plain code and the workflow resolved it on small
  accounts and asked for the order number on large ones, where older orders contain the same mug set. Asking is
  defensible, but the recent order is the only one inside the returns window; graded "wrong" as the case specifies.

**Resolved (6 random runs, seed 7):** all correct. One reply listed card types beyond the question; they are in the
policy.

## What the grader does not check

- Invented details in replies are not penalised unless they contradict a required fact. In the runs read, I found none
  that contradicted the policy.
- Tone and length are not scored.
