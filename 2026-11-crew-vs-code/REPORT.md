# Multi-agent swarms or a boring state machine? Report

1 November 2026. Design: [README.md](README.md), pushed with the build and both pilots before the measured run
(b41f522c). Full numbers: [results/analysis.md](results/analysis.md). Checks: [results/checks.md](results/checks.md).
Every run's actions, reply, grade, handoffs and cost: `results/main/runs.jsonl.gz`; the judge's labels:
`results/main/judge.jsonl.gz`.

## 1. What I wanted to find out

"Multi-agent swarms are the future" is a common claim. When does a 3-agent crew that hands work between specialists
beat a typed schema plus plain `if`/`else` code (a state machine), or a single agent with all the tools, on customer
emails? What does each cost?

## 2. Why I thought it was worth testing

Crews of agents with handoffs (OpenAI's Swarm and Agents SDK, CrewAI) are a popular way to build support bots. They
are sold on splitting a job between specialists. [need-an-agent](../2026-10-need-an-agent/) found that a single agent
was rarely needed over plain code on this shop's emails. This experiment adds the crew and gives it the cases where
splitting should help most: emails with two or three requests that span both specialists (level 6).

## 3. What I predicted

Fixed before any run (for each model, Luna primary, Qwen as replication):

1. **H1 (where code should win):** on levels 1 to 3, the state machine resolves more emails than the shared-history
   crew.
2. **H2 (where the crew should win):** on level 6, the shared-history crew resolves more than the single agent.
3. **H3 (handoff style):** the shared-history and note-only crews differ over all levels.

The pilots already pointed against H2. The hypotheses were kept as written.

## 4. How I tested it

- **The shop:** need-an-agent's simulated homeware shop, policy, nine tools, faults and grader, unchanged.
- **Cases:** 38 customer emails in six levels:
  - **1 simple:** a lookup or a policy question.
  - **2 multi-step:** a clear refund or replacement.
  - **3 branching:** the outcome depends on what the lookups return.
  - **4 recovery:** a tool fails or the input is slightly off.
  - **5 other requests.**
  - **6 compound (new):** two or three requests in one email, across both specialists' areas.
- **Variation:** each case ran in its original wording and a paraphrase, with a small and a large customer account.
- **Four architectures:**
  - **State machine:** one model call fills a typed list of requests. Plain code applies the policy to each one, and
    a second call writes the reply. Always 2 calls.
  - **Single agent:** the model in a loop with all nine tools and the whole policy.
  - **Crew, shared history:**
    - A front desk (can look things up, can't change anything), a delivery specialist and a returns specialist.
    - Each has its own tools and its own sections of the policy, plus `transfer_to_<agent>` tools.
    - The agent receiving a transfer sees the whole conversation, as in OpenAI's Swarm and Agents SDK.
    - The instructions start with the Agents SDK's own handoff prompt.
  - **Crew, note only:** the same crew, but the agent receiving a transfer sees only the email and the note, as in a
    CrewAI task hand-off.
- **Models:** `openai/gpt-6-luna` and `qwen/qwen3.7-flash` through OpenRouter, default settings.
- **Size:** 38 cases × 2 wordings × 2 account sizes × 5 repetitions × 4 architectures × 2 models = **6,080 runs**.
- **Measures:**
  - **Resolved:** exactly the right changes to orders, and every required fact in the reply.
  - **Harmful:** a refund, replacement, cancellation or address change the policy didn't call for.
  - **False action claims:** the reply says something was done that the shop's log shows wasn't. A judge model
    labelled these; I hand-checked every positive and a tenth of negatives, and agreed with all 916.
  - Cost, model calls, time and consistency.

## 5. What happened

**Emails resolved** (share of runs: 400 per row on levels 1–3, 120 on level 4, 120 on level 6, 760 in all; higher is better; 95% interval for the total):

| Architecture | Levels 1–3 | Level 4 recovery | Level 6 compound | All levels |
| --- | --- | --- | --- | --- |
| State machine, Luna | 97.0% | 67% | **100%** | **93%** (91–95) |
| Single agent, Luna | 99.8% | 78% | 96% | **96%** (94–97) |
| Crew, shared history, Luna | 92.2% | 65% | **62%** | **81%** (78–83) |
| Crew, note only, Luna | 99.5% | 71% | 86% | **91%** (89–93) |
| State machine, Qwen | 95.5% | 67% | **94%** | **91%** (89–93) |
| Single agent, Qwen | 94.2% | 71% | 80% | **89%** (87–91) |
| Crew, shared history, Qwen | 82.2% | 47% | **39%** | **70%** (67–73) |
| Crew, note only, Qwen | 86.5% | 49% | 58% | **75%** (72–78) |

Levels 1–3 are pooled; each level, and level 5, is in the analysis.

**Replies claiming an action that wasn't taken** (share of runs; lower is better):

| Architecture | Luna | Qwen |
| --- | --- | --- |
| State machine | 0% | 0% |
| Single agent | 0% | 1% |
| Crew, shared history | **11%** | **17%** |
| Crew, note only | 2% | **13%** |

**Harmful runs** (count of 760; lower is better): state machine 0 and 0; single agent 2 (Luna) and 27 (Qwen); crew
shared 0 and 24; crew note 2 and 16.

**The hypotheses** (difference in resolved, percentage points; Holm-adjusted permutation p):

| Hypothesis | Luna | Qwen | Verdict |
| --- | --- | --- | --- |
| H1: state machine > crew (shared), levels 1–3 | +4.7, p = 0.0008 | +13.2, p = 0.0003 | **Supported** for both models |
| H2: crew (shared) > single agent, level 6 | −34.2, p = 1.0 | −40.8, p = 1.0 | **Not supported.** The crew was far worse, not better |
| H3: crew (shared) ≠ crew (note), all levels | −10.3, p = 0.0003 | −5.1, p = 0.014 | **Supported.** Note-only handoffs did better |

**Cost and speed** (per run; lower is better):

| Architecture | Luna cost | Qwen cost | Model calls | Luna median time | Same result in all 5 repeats (Luna; higher is better) |
| --- | --- | --- | --- | --- | --- |
| State machine | $0.00018 | $0.00043 | 2.0 | 4.5 s | 99% |
| Single agent | $0.00023 | $0.00022 | 3.9–4.0 | 7.9 s | 90% |
| Crew, shared history | $0.00049 | $0.00042 | 4.5 | 10.0 s | 69% |
| Crew, note only | $0.00048 | $0.00046 | 5.4–5.7 | 10.5 s | 84% |

All 6,080 runs cost $2.20, and the judge $0.52.

## 6. What surprised me

- **The crew was worst exactly where it was supposed to win.** On the compound emails, the shared-history crew
  resolved 62% with Luna, against 100% for the state machine and 96% for the single agent. With Qwen it resolved 39%.
- **Crews tell customers things are being handled when nobody is handling them.**
  - Typical reply: "I've passed your address change to our delivery team; they'll be in touch within 1 working day."
    There was no escalation, and the delivery specialist never received the request.
  - In 20 of the 23 Luna level-6 runs that left a request undone, the last agent was the returns specialist. It did
    its own part, then wrote that the rest had been passed on instead of transferring it.
  - The single agent and the state machine almost never did this (0–1% of runs).
- **Sharing the whole conversation made the crew worse, not better.** Before the pilots I expected full history to
  help. It did worse than a short note with both models. I didn't measure why. The run records keep only the actions, the
  hand-overs and the reply, not each agent's messages.
- **Specialisation itself caused errors.** Specialists only had their own sections of the policy. In some runs a
  specialist sent a general policy question ("do you take Amex?", "how long do refunds take?") to the billing team as
  an escalation, because it couldn't see the answer.
- **Crews redid each other's work.** With Qwen, 34 crew runs did the same action twice (a second refund, a second
  replacement). One run refunded the same blanket five times.
- **The boring version was the safest.** The state machine never did anything harmful and gave the same result in
  99% of repeated conditions with Luna. Its losses were deliberate: it never retries a failed write, so it escalated
  every level-4 email where the refund or replacement service failed once (L4-03, L4-04). It also asked for an order
  number when a paraphrase didn't name the item clearly enough to find the order (L3-06).

## 7. What this might mean in practice

### Impact

For a support inbox with a known set of request types, a typed schema plus plain code did as well as an agent and
better than a crew, at the lowest cost and with no harmful actions. A single agent was the best all-rounder with the
stronger model, mainly because it can retry and recover (level 4). A 3-agent crew with handoffs cost about twice as
much, was less consistent and resolved fewer emails. Its customers were also more often told that something was
being dealt with when it wasn't.

The crew's failure isn't the model being weak. The same model, given all the tools, did the job. The failure is in the
hand-over: who writes the final reply, and whether "I've passed it on" means anything.

### Configuration recommendations

| Recommendation | Why | Strength |
| --- | --- | --- |
| For a fixed set of request types, start with a typed schema + code, not agents | Matched or beat the crew on levels 1–3 with both models; 0 harmful runs; cheapest | Strong: H1, Holm p ≤ 0.0008 |
| Don't split one customer conversation across a crew of specialist agents to handle multi-request emails | The crew resolved 34–41 points fewer compound emails than one agent with all tools | Strong: H2 tested and reversed |
| If you do use a crew, hand over a written note, not the whole conversation | Note-only resolved 5–10 points more and made fewer false claims with Luna (2% vs 11%) | Strong: H3, Holm p ≤ 0.014 |
| Don't give agents a way to say "passed to a team" that isn't a real action. Make hand-offs to people a tool call, and check replies against the action log before sending | 202 of the false claims were "passed to a team" with nothing logged | Descriptive |
| Make one component own the final reply and check that every request in the email has an outcome | Level-6 crew replies left out requests and facts that earlier agents had dealt with | Descriptive |
| Never let agents retry a failed write blindly; make writes idempotent or check before retrying | Repeated refunds and replacements in 47 harmful runs (crews and the Qwen single agent) | Descriptive; same as need-an-agent |

### Risks this exposes

- **Silent drops look like service.** A customer told "a colleague will be in touch" waits for someone who was never
  told. Without comparing replies with the action log, the operator wouldn't see it either.
- **More agents, more places to lose state.** Each hand-over can drop a request, repeat an action or lose a fact.
- **Specialist policies create gaps.** Giving each agent only "its" part of the policy means questions that cross
  the boundary get escalated or answered wrongly.

## 8. What the experiment does not prove

- **I wrote the shop, cases, state machine and crew,** and I knew the cases while writing the state machine's schema.
  A real inbox has requests no schema anticipates; here those would be escalated.
- **One crew design.** A manager agent that calls specialists as tools, other roles, or a stronger model could do
  better. The handoff prompt and the transfer result are the Agents SDK's own; the roles and policy split are mine.
- **One small domain that suits a state machine, and two cheap models at default settings.**
- **The false-claim judge is one of the models under test,** though all 916 labels I checked agreed with it.

## 9. What I'd test next

- **A manager-and-tools crew:** one agent that calls specialists as tools and writes the reply itself, against the
  handoff crew and the single agent.
- **A reply check:** code that compares every "done" and "passed on" in a reply with the action log before sending,
  and what that does to false claims in each architecture.
- **Requests outside the schema,** to measure how often the state machine has to escalate what an agent would have
  handled.

## 10. How to reproduce the results

```
python3 -I src/validate.py                        # the level-6 cases and the grading change, no model
python3 -I src/run.py <out> --reps 5              # 6,080 runs; needs ~/.config/openrouter.key
python3 -I src/judge.py <out>                     # false action claims
python3 -I src/analyse.py <out> > results/analysis.md
python3 -I src/analyse.py results/main            # the same tables from the exported data
```

## 11. What changed from the design

- **Nothing in the cases, architectures, measures or hypotheses changed after the design was pushed.**
- **Two scripts were written after the design push, during the main run:** `judge.py` (the false-action-claim judge
  and its prompt) and `analyse.py` (the tables and tests). Interim resolved rates from the run's progress were visible
  while I wrote them. Both implement the measures and tests the design already described; the judge's mapping of
  claims to log entries is in `analyse.py`.
