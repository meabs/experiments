# Do you actually need an AI agent?

**Status: design, written 2026-10-30 before the measured run.** A proof of concept for an architecture article on
Programming the Loop (like 2026-10-agent-identity), not a hypothesis test: the results are rates per architecture and
level, with Wilson 95% intervals, and no significance tests. Three small pilots (864 runs, $0.24) checked the harness;
they are described under [Pilots](#pilots) and are not part of the results. Later changes go in the amendment log.

## Question

A small online shop wants software to answer customer-service emails and act on them (refunds, replacements,
cancellations). There are four ways to build it, each a step up in complexity:

1. **Plain code:** no AI. Keyword rules, the policy in `if` statements, template replies.
2. **One model call:** code gathers everything about the customer, one model call decides what to do and writes
   the reply, code carries it out.
3. **Workflow:** fixed code steps, with the model used at fixed points: one call to read the email into fields, the
   policy checked in code, one call to write the reply.
4. **Agent:** the model works in a loop with the tools and decides its own steps.

Which architecture handles which kind of request? Where does each one stop being good enough, and what does each cost
in money, time, consistency and code? The experiment is built so that every architecture has requests it should win
(the simple ones should suit plain code and workflows; recovery and unexpected requests should suit the agent), so the
interesting result is where the crossovers fall, not a single winner.

## What I expect (written before the main run, so the results can contradict it)

- Plain code is fine on simple and fixed requests in the wording it was written for, worse on paraphrased emails, and
  can't do levels 4 and 5.
- The workflow is at or near the ceiling on levels 1 to 3, escalates most of level 5 (by design), and recovers from
  read failures but not write failures (by design).
- The agent is best on levels 4 and 5, and costs more and varies more.
- The one-call version matches the agent on small accounts (it sees everything), but its cost grows with account size.
- The cheap model (Qwen) is closer to Luna in the workflow than in the agent, because the workflow gives it less to
  decide.

## The shop

Everything is simulated in Python ([`src/shop.py`](src/shop.py)); nothing touches a real system.

- **Hartley & Finch**, a UK homeware shop: 8 customers, 14 products (2 out of stock, 1 on final sale), 15 orders in
  different states (processing, in transit, delivered, stuck at a depot), one order paid twice.
- **Policy:** [`src/policy.md`](src/policy.md), one page: 30-day returns, refunds straight away, final-sale items, a
  £200 limit above which a manager approves, damaged items (refund or replacement; out of stock means refund),
  deliveries (where is it, delivered but not received, lost in transit), address changes and cancellations while
  processing, no holding orders, billing problems go to the billing team, and act only for the account's own email
  address.
- **Tools**, the same for every architecture: `find_customer`, `get_order`, `track_shipment`, `check_stock`,
  `issue_refund`, `send_replacement`, `change_address`, `cancel_order`, `escalate`. They behave like services: errors
  come back as HTTP-style status codes. Like many real payment integrations, the refund service doesn't stop a
  duplicate refund.
- **Account size:** each case runs with **small** accounts (1 to 3 orders per customer) and **large** accounts (40 older
  orders added to every customer, fixed seed, all outside the 30-day window, some with the same products). Large
  accounts make "fetch everything first" expensive and make it harder to tell which order a customer means.

## The 32 cases

[`src/cases.py`](src/cases.py): one customer email each, with the outcome the policy requires (the state changes, and
facts the reply must contain). Written before any architecture was run.

| Level | Cases | What it tests | Examples |
| --- | --- | --- | --- |
| 1 simple | 6 | One lookup, or a policy question | Where is A1051? Do you deliver to Ireland? |
| 2 multi-step | 6 | A clear refund or replacement, everything stated | Refund the tea towel from A1042 |
| 3 branching | 8 | The outcome depends on what the lookups return | Outside 30 days; final sale; £240 rug (escalate); replacement asked but out of stock; delivered but not received; no order number given; tracking stuck for two weeks; written from a different email address |
| 4 recovery | 6 | A tool fails or the input is slightly off; the right outcome is as if nothing went wrong | Tracking 503 once; order number written `#a-1042`; refund times out *after* going through; warehouse 503 once; order lookup 500 once; email address in different letter case |
| 5 unanticipated | 6 | Requests outside the workflow's four intents, still covered by the policy | Change address; cancel; two requests in one email; double charge; "hold my order"; two damaged items with different wishes |

**Two wordings of every email.** I wrote the plain-code keyword rules after reading the original emails, which flatters
plain code. So every case also runs in a **paraphrased** wording written by a model not under test
(google/gemini-3.1-flash-lite; [`src/paraphrase.py`](src/paraphrase.py), [`cases/paraphrased.json`](cases/paraphrased.json)).
I read all 32 paraphrases: each keeps the order numbers, items, requests and preferences, and none needed correcting.

## The four architectures

All use the same tools, the same policy text and, for the AI ones, the same model per run. Lines of code exclude the
shared shop and tools (non-blank, non-comment lines).

| Architecture | Files | Lines | Model calls per email | How it handles errors |
| --- | --- | --- | --- | --- |
| Plain code | [`core.py`](src/core.py) + [`rules.py`](src/rules.py) | 204 | 0 | Reads retried twice on 5xx; unknown order number: search the customer's orders by item; writes never retried (a failed write is escalated, so money can't go twice); anything not one of the four intents is escalated |
| One model call | [`single.py`](src/single.py) | 53 | 1 | Gathers the customer, all their orders, tracking and stock first; carries out the model's actions in order; any failed action is escalated with a holding reply |
| Workflow | [`core.py`](src/core.py) + [`workflow.py`](src/workflow.py) | 165 | 1 or 2 | As plain code; the model reads the email into fields and writes the reply |
| Agent | [`agent.py`](src/agent.py) | 34 | As many as it needs (limit 15) | Whatever the model decides; at the step limit, escalated with a holding reply |

**What the workflow (and plain code) were built for.** A developer building it would start from the shop's common
requests, so they handle four intents: *delivery status* (where is it, never arrived, stuck), *return or refund*,
*damaged item*, and *policy question*. Anything else is escalated to a person. That fallback is deliberate and
realistic: it is safe, but someone has to do the work.

**Models** (via OpenRouter, the cost-effective tier, billed price recorded per call):

- `openai/gpt-6-luna`: $0.10 per million input tokens, $0.50 output;
- `qwen/qwen3.7-flash`: $0.03 / $0.13.

Default temperature and reasoning settings. Plain code uses no model.

## Measures

Per run ([`src/grade.py`](src/grade.py)), from the shop's record of state changes and the reply:

- **Outcome**, one of:
  - **resolved:** exactly the right state changes, and the reply contains every required fact;
  - **harmful:** a refund, replacement, cancellation or address change the policy didn't call for (wrong order, wrong
    item, or a duplicate), whatever else happened;
  - **escalated:** handed to a person when the policy didn't require it, with nothing harmful (safe but unresolved);
  - **wrong:** anything else (missed action, missing or wrong information, a needed escalation not made).
- **Cost** (OpenRouter's billed cost), **model calls**, **tokens**, **wall time**.
- **Consistency:** the share of case × wording conditions where all repetitions ended the same way.
- **Code size** (above) and, in the article, what each architecture would need changed to handle a new kind of request.

The grader was validated before any model run ([`src/validate.py`](src/validate.py)): for every case, the expected
actions run without error and score as resolved with a reference reply; doing nothing isn't counted as right where
action is needed; a doubled state change is harmful; an empty reply fails the facts.

## Size and order

- **32 cases × 2 wordings × 2 account sizes × 5 repetitions = 640 runs per architecture-and-model**, 7 combinations
  (plain code has no model): **4,480 runs.**
- From the pilots: about **$1.40** in total, roughly an hour with 8 runs in parallel.
- Runs go in a shuffled order (seed 1), so no architecture always runs at the same time.
- A run that crashes is recorded as "crashed".

## Pilots

Not part of the results. They found four faults in my materials, fixed before the main run:

1. **Pilot 1** (192 runs, original wording, small accounts, 1 repetition, $0.04):
   - **The policy was ambiguous.** Luna's agent told two customers how to send an item back instead of refunding it,
     because the policy said "can be returned for a refund" without saying when. The policy now says to refund
     straight away (prepaid label in the parcel).
   - **Two fact patterns were too strict:** "30-day returns period" and "escalated to a manager" are correct but didn't
     match. Both patterns were widened.
   - **L4-02's wrong order number wasn't a fair test.** "A1024" for A1042 made "please confirm the number" a defensible
     answer. It became a formatting slip, "#a-1042", which has one right answer.
   - **Grading:** a refund that went through but was then escalated scored as "wrong"; it is now "escalated" (safe
     hand-off).
2. **Pilot 2** (448 runs, both wordings, small accounts, 1 repetition, $0.10): the fixes worked. Levels 1 to 3 are near
   the ceiling for every AI architecture (as expected). The differences are in levels 4 and 5. The one-call version
   matched the agent overall on small accounts, which is why large accounts were added.
3. **Pilot 3** (224 runs, original wording, large accounts, $0.09): the one-call version's median prompt grew to
   11,172 tokens (Luna), against the agent's 5,536 and the workflow's 394. No crashes in any pilot.

## Threats to validity

- **I wrote the shop, the policy, the cases and all four architectures.** The workflow and plain code were written
  with knowledge of the case types, which flatters them on levels 1 to 4. The paraphrased wording counters this for
  the language side only.
- **One small domain.** Customer service is a natural fit for a workflow. Other domains (open-ended research, coding)
  favour agents more.
- **The one-call version's "fetch everything" only works because the shop is small**; large accounts test one way it
  stops working, not all.
- **Exact-match grading.** A reply that is helpful but omits a required fact counts as wrong; the required facts are
  short and lenient (dates in any common form).
- **Two models, default settings, five repetitions.** Intervals are wide for single levels.

## Reproducing

```bash
python3 -I src/validate.py                         # cases and grader, no model
python3 -I src/paraphrase.py                       # cases/paraphrased.json (already committed; costs < $0.01)
python3 -I src/run.py <out> --reps 5               # 4,480 runs; needs ~/.config/openrouter.key
python3 -I src/analyse.py <out> > results/analysis.md
```

## Amendment log

- 2026-10-30: the user asked for this as an architecture article: "This should be an architecture article Do you
  actually need an agent? (beginner) Agreed. Include tasks with branching or recovery, where the agent should win."
  Models via OpenRouter, "use cost effective models".
