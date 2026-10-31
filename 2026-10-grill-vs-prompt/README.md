# Grilling or a good prompt? Does the skill beat a short instruction to clarify first?

**Final design, committed 2026-10-31 before any measured run.** Later changes go in the amendment log at the
bottom.

## Why

[Grill me first? (GRL)](../2026-10-grilling/) found that Matt Pocock's
[`grilling`](https://github.com/mattpocock/skills/tree/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/skills/productivity/grilling)
skill recovered all five rules that only the developer knew, in every run, and the ticket alone recovered none. The
gain came entirely from the developer correcting one or two wrong recommendations.

But the only cheap alternative it tested was a one-line "Before you start, ask me anything you need to know", which
never asked anything. An outside review of GRL put the gap plainly: it showed the value of *compulsory, structured*
clarification, not yet the extra value of this particular skill. A short instruction that makes the agent list the
open decisions and wait might get most of the benefit with less reading.

Following the backlog rule, this isn't designed to show the simple approach wins. Grilling walks a design tree one
branch at a time, over as many rounds as it takes, so it *should* win where a single list of questions can't reach:
when there are many unknowns, and when answering one question opens new ones. The question is where that crossover
is.

## Questions

1. On tickets whose unknowns are few and independent, does a short structured prompt recover the developer-only rules
   as well as the grilling skill, for less developer reading?
2. On tickets where one answer opens new questions (nested unknowns), does grilling beat the structured prompt?
3. Does a targeted interview capped at three questions keep up when there are more than three unknowns, or nested
   ones?
4. What does each approach cost the developer (questions, words read, words typed) and the agent (tokens, time)?

## Arms

| Arm | Opening message, after the ticket | Skill installed |
| --- | --- | --- |
| **T** ticket only | (none) | none |
| **G** grilling | "Grill me on this before you build it." | `grilling` (as in GRL) |
| **S** structured prompt | "Before writing any code, list every decision this ticket leaves open that you can't settle from the code, each with your recommended answer. Then stop and wait for my reply." | none |
| **K** targeted interview | "Before writing any code, ask me at most three questions: the ones whose answers would change the code most. Then stop and wait for my reply." | none |

S and K are written to be what a developer could type without installing anything. Both may ask again after the
developer's reply; nothing stops them, and nothing prompts them to. Whether they do is part of what's measured.

## Agent, repository and rig

Unchanged from GRL: Codex CLI 0.157.0 with hosted `gpt-5.6-luna` at medium reasoning effort, subagents on
(`multi_agent_v2`) in every arm, the bubblewrap sandbox (hidden tests and briefs invisible), one Codex session per run
with each developer reply sent through `codex exec resume`, and the stall watchdog from GRL's amendment log (a turn
idle for 2 minutes inside a collaboration `wait` is ended and counted). Skills pinned to mattpocock/skills `4ae2317`,
in the run's `.agents/skills/` only, with an otherwise empty Codex home. The repository is sec-authz's accounts
service with GRL's starter overlay.

## Tasks

Seven tickets, each leaving out requirements that are either findable in the repository ("in the repo") or known only
to the developer ("in my head"). There are **15 distinct in-my-head rules**, three times as many as GRL, so that
results can be reported per rule.

| Level | Tasks | Left out (repo / head) | In-my-head rules |
| --- | --- | --- | --- |
| **Few, flat** | S1, S2, L1, L2 (from GRL, unchanged) | 2–4 (1–2 / 1–2) | S1 rb, S2 rb, L1 rc, L1 rd, L2 rc (5) |
| **Many, flat** | M1 change an account's daily limit (new) | 6 (2 / 4) | rc support can only lower it; rd £5,000 ceiling; re savings accounts fixed; rf audit note with old and new limit (4) |
| **Nested** | N1 goodwill credits (new) | 4 (1 / 3) | rb over £100 waits for approval (parent); rc how approval works (child); rd you can't approve your own (child) (3) |
| **Nested** | N2 approve closure requests (new) | 5 (2 / 3) | rc money must be moved to another account first (parent); rd where it can go (child); re how the move is booked (child) (3) |

L2 rd stays labelled "guessable", as in GRL's amendment log: it counts towards all left-out requirements but isn't
one of the 15.

In a **flat** ticket each rule is its own topic, settled by its own question. In a **nested** ticket the parent rule's
answer opens a new part of the design (an approval step, a transfer of money), and the child rules are decisions inside
it that only come up once the agent knows that part exists. The briefs fix how this is answered (below).

Briefs, hidden tests and references are in `tasks/`, `hidden/` and `reference/`. Every reference meets every
requirement, and the untouched app passes no ticket (`scripts/check_references.sh`).

## The developer

As in GRL, **Claude (the assistant running these experiments) plays the developer**, from a private brief per task,
with GRL's fixed reply rules:

- answer the question asked, briefly; no requirements the question didn't touch;
- "yes" to a recommendation that agrees with the brief or that it has no view on; correct one that contradicts it with
  the brief's rule;
- point to the code for questions about facts in the repository;
- an open question ("anything else?") gets the top-of-mind requirement if it hasn't come up, otherwise "no, that's
  it";
- "your call" for things the brief doesn't care about;
- after 6 rounds, "that's enough, go with your recommendations" (counted).

Added for this experiment:

- **Nesting.** A question that touches a parent rule gets the parent rule in one or two sentences and nothing about its
  children. A child rule is given only when the agent asks about, or recommends an answer on, that child's own decision.
  Each nested brief spells out what the parent answer says.
- **Proceeding.** When the agent says it has what it needs and asks to go ahead, the reply is "Yes, go ahead." If it
  builds without waiting, that's recorded, not prompted.

The relay gives each interview run an anonymous ID in shuffled order, and a judge model (`openai/gpt-6-luna` through
OpenRouter) audits every reply against its brief for anything given that the agent's message didn't touch, as in GRL,
with the nesting rule added to its instructions.

## Measures

- **Main: in-my-head rules met.** Hidden tests per rule, counted only in runs that pass the ticket's own tests.
  Reported **per rule** (15 rules × 5 runs per arm), and as the mean per run.
- **All left-out requirements met**, and ticket pass rate.
- **Wrong assumptions that reached the code.** For each in-my-head rule a run missed: was it never raised (a silent
  assumption), raised but not settled, or settled but built wrong? And **wrong recommendations caught**: recommended
  answers that contradicted the brief and that the developer had to correct.
- **Developer's cost:** rounds, questions asked, words the developer read, words typed.
- **Agent's cost:** tokens (input, cached, output, reasoning), list-price cost, wall time. Stalls per arm.

## Hypotheses (fixed before any run)

1. **Non-inferiority on flat tickets.** On the few- and many-flat tickets (S1, S2, L1, L2, M1: 9 rules), S is no worse
   than G by more than 0.15 in the proportion of in-my-head rule checks met. Unit: the rule. For each rule, the
   difference S − G in the proportion of its 5 runs that met it; the mean over rules, with a one-sided 95% lower bound
   from a two-stage bootstrap (resample rules, then runs within each rule and arm; 10,000 resamples, seed 1). S is
   non-inferior if the lower bound is above −0.15.
2. **Nested tickets favour grilling.** On N1 and N2, G meets more in-my-head rules per run than S.
3. **The three-question cap loses past three unknowns.** On M1, N1 and N2, G meets more in-my-head rules per run than
   K.
4. **The prompts cost the developer less.** Across all tickets, S (4a) and K (4b) each make the developer read fewer
   words per run than G.

Hypotheses 2, 3, 4a and 4b use a permutation test stratified by task (10,000 permutations, seed 1) on per-run values,
Holm-adjusted across the four. Hypothesis 1 is judged on its own criterion. A test that isn't significant is reported
as "no measurable difference", and identical results as identical, not as equivalence; only hypothesis 1 can support
a claim that S is about as good as G, and only within its margin.

Everything else is description: the level × arm table (where each approach stops keeping up), T against the rest, K
against S, and the per-rule table.

## Size

7 tasks × 4 arms × 5 runs = 140 runs: 35 ticket-only runs (scripted) and 105 interviews I answer. At GRL's per-run
cost this is about $3–4 of agent time at list prices, plus the audit.

## Before the runs

- **Brief check:** a fresh reader (a judge model through OpenRouter, not me) reads each new ticket (M1, N1, N2) with
  its brief and says whether each left-out item is something a reasonable colleague would ask about or know, and
  whether anything in the ticket or repository already gives an in-my-head rule away. S1–L2 were checked in GRL.
  Anything marked unreasonable is replaced.
- **Pilot for the ceiling:** T on every task, 2 runs each. If T meets an in-my-head rule, the ticket or repository is
  giving it away, and it's fixed (or relabelled guessable, with the user's agreement) before the main run.
- **Dry run:** one S and one K interview on N1, and one G on N2, to check the openers behave as intended, the nesting
  rule can be followed, and the audit handles it. Not counted.

## Limits, stated now

- **The developer is me, following a brief.** It knows the complete answer and corrects every wrong recommendation, so
  this measures how well each approach extracts what the developer knows, not how well it copes with a real person
  who forgets, guesses or disagrees.
- **One agent, one repository, seven tickets, 15 rules.** Better than GRL's five, still small.
- **I wrote the tickets, the rules and the nesting.** The brief check guards against tricks; which rules I chose still
  shapes the result.
- **One wording each for S and K.** A better-written prompt might do better; these are written to be what a developer
  would plausibly type.

## Amendment log

- 2026-10-31: design written at the user's request ("Do it"), following an outside review of GRL that proposed this
  comparison, and my plan in reply (four arms; few-flat, many-flat and nested tickets; about 15 distinct rules; 5 runs
  per cell with a pre-registered margin).
