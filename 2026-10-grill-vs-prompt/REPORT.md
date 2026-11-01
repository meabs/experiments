# Grilling or a good prompt? Report

1 November 2026. Design: [README.md](README.md), committed and pushed (e33d6e20) before any run; the brief check,
pilot and dry run were pushed (80be09cb) before the main run. Full numbers: [results/analysis.md](results/analysis.md);
checks: [results/checks.md](results/checks.md); every run's dialogue, labels, grade and diff: `results/main/`.

## 1. What I wanted to find out

[Grill me first? (GRL)](../2026-10-grilling/) found that Matt Pocock's `grilling` skill recovered the rules only the
developer knew, and that a one-line "ask me anything first" never asked a question. An outside review pointed out what
that didn't show: whether the *skill* is needed, or whether a short instruction that makes the agent list its open
decisions and wait gets the same result. So:

1. On tickets whose unknowns are few and independent, does a short structured prompt recover the developer-only rules
   as well as the grilling skill, for less reading?
2. On tickets where one answer opens new questions (nested unknowns), does grilling beat the structured prompt?
3. Does a targeted interview capped at three questions keep up when there are more than three unknowns, or nested ones?
4. What does each cost the developer and the agent?

## 2. Why I thought it was worth testing

If a two-sentence prompt does what the skill does, developers can skip installing and learning one more tool. If it
doesn't, the experiment should show where the skill earns its place. Following the backlog rule, the tickets were
built so that grilling *should* win somewhere: on tickets with many unknowns, and on nested ones, where its
one-branch-at-a-time walk through the design should reach decisions a single list can't.

## 3. What I predicted

Fixed before any run (README):

1. **On flat tickets, the structured prompt (S) is no worse than grilling (G)** by more than 0.15 in the proportion of
   developer-only rule checks met (non-inferiority, rules as the unit).
2. **On nested tickets, G beats S.**
3. **On the many-unknown and nested tickets, G beats the three-question interview (K).**
4. **S (4a) and K (4b) make the developer read fewer words than G.**

## 4. How I tested it

- **Agent:** Codex CLI 0.157 with hosted `gpt-5.6-luna` at medium effort, one session per run, each developer reply
  sent back into it; bubblewrap sandbox, hidden tests and briefs invisible; the same rig as GRL.
- **Four arms**, each the ticket plus:
  - **T:** nothing.
  - **G:** "Grill me on this before you build it." with `grilling` installed (mattpocock/skills `4ae2317`).
  - **S:** "Before writing any code, list every decision this ticket leaves open that you can't settle from the code,
    each with your recommended answer. Then stop and wait for my reply."
  - **K:** "Before writing any code, ask me at most three questions: the ones whose answers would change the code
    most. Then stop and wait for my reply."
- **Seven tickets on the accounts API, 15 distinct rules only the developer knew:**
  - **Few, flat** (S1, S2, L1, L2 from GRL): 5 rules, one or two per ticket.
  - **Many, flat** (M1, change a daily limit): 4 rules, each its own topic (support can only lower it; a £5,000
    ceiling; savings accounts are fixed; an audit note).
  - **Nested** (N1 goodwill credits, N2 approving closure requests): 3 rules each. A parent rule (credits over £100
    wait for approval; money left in an account has to be moved first) opens a part of the design whose two child
    rules only come up once the agent knows it exists.
- **The developer was Claude following a fixed brief per ticket**, with GRL's reply rules plus a nesting rule: a
  question that touches a parent gets the parent rule in a sentence and nothing about its children. A separate judge
  model audited every reply: no leak in 103 of 105 interviews; the two it flagged (K on L2) don't change any
  hypothesis (results/checks.md).
- **Scoring:** hidden tests per rule, counted only in runs that passed the ticket's own tests.
- **Size:** 7 tickets × 4 arms × 5 runs = 140 runs, 105 of them interviews. Agent cost $2.81 at list prices.

## 5. What happened

**Developer-only rules met** (rule checks: rules × 5 runs; higher is better):

| Level | Rules | T ticket only | G grilling | S structured prompt | K three questions |
| --- | --- | --- | --- | --- | --- |
| Few, flat | 5 | 0 / 25 | 21 / 25 | 21 / 25 | 19 / 25 |
| Many, flat | 4 | 0 / 20 | 10 / 20 | 9 / 20 | 6 / 20 |
| Nested | 6 | 0 / 30 | 3 / 30 | 5 / 30 | 0 / 30 |
| **All** | 15 | **0 / 75** | **34 / 75** | **35 / 75** | **25 / 75** |

Every one of the 140 runs passed its ticket's own tests.

**Per rule** (runs that met it, of 5; higher is better):

| Ticket | Rule | T | G | S | K |
| --- | --- | --- | --- | --- | --- |
| S1 | support may only add internal notes | 0 | 2 | 1 | 0 |
| S2 | resolution saved as a customer-visible comment | 0 | 4 | 5 | 5 |
| L1 | support can freeze, only admins unfreeze | 0 | 5 | 5 | 5 |
| L1 | audit note on freeze and unfreeze | 0 | 5 | 5 | 4 |
| L2 | new assignee must be assigned to the account | 0 | 5 | 5 | 5 |
| M1 | support can only lower the limit | 0 | 5 | 5 | 5 |
| M1 | £5,000 ceiling | 0 | 4 | 3 | 1 |
| M1 | savings accounts fixed | 0 | 0 | 0 | 0 |
| M1 | audit note with old and new limit | 0 | 1 | 1 | 0 |
| N1 | over £100 waits for approval (parent) | 0 | 1 | 2 | 0 |
| N1 | how approval works (child) | 0 | 1 | 2 | 0 |
| N1 | can't approve your own (child) | 0 | 1 | 1 | 0 |
| N2 | money must be moved first (parent) | 0 | 0 | 0 | 0 |
| N2 | where the money can go (child) | 0 | 0 | 0 | 0 |
| N2 | the move is booked on both accounts (child) | 0 | 0 | 0 | 0 |

**The hypotheses:**

| Hypothesis | Result | Statistic | Verdict |
| --- | --- | --- | --- |
| 1. S no worse than G on flat tickets (margin −0.15) | S − G = −0.02 per rule | one-sided 95% lower bound −0.13 | **Supported**, narrowly: within the margin |
| 2. G beats S on nested tickets | G − S = −0.20 rules per run | Holm p = 1.0 | **Not supported**: no measurable difference, and S was slightly ahead |
| 3. G beats K on many-unknown and nested tickets | G − K = +0.47 rules per run | Holm p = 0.17 | **Not supported**: no measurable difference at this size |
| 4a. S makes the developer read less than G | −337 words per run | Holm p = 0.0004 | **Supported** |
| 4b. K makes the developer read less than G | −567 words per run | Holm p = 0.0004 | **Supported** |

**What it cost** (per run, mean; lower is cheaper):

| | G grilling | S structured prompt | K three questions | T ticket only |
| --- | --- | --- | --- | --- |
| Rounds the developer answered | 2.4–2.6 | 1.0–1.2 | 1.0 | 0 |
| Questions asked | 10–13 | 8–10 | 3 | 0 |
| Words the developer read | 599–718 | 266–351 | 70–101 | 0 |
| Words the developer typed | 34–70 | 39–60 | 27–51 | 0 |
| Agent wall time | 2.8–3.6 min | 1.4–1.7 min | 1.2–1.8 min | about 1 min |
| Agent cost, list price | $0.026–0.031 | $0.019–0.021 | $0.014–0.019 | $0.016–0.017 |

Ranges run across the three levels.

**Why rules were missed.** Almost never because the agent built the wrong thing after asking. Of the rule checks each
interview arm missed, G's 41 were all rules its dialogue never raised, S's 39 of 40, K's all 50. Asking about the right
thing was the whole game.

## 6. What surprised me

- **The structured prompt matched the skill at half the reading.** S met 35 of 75 rule checks to G's 34, in one round
  instead of two or three, with about 300 words to read instead of about 650, and at two-thirds of the agent cost.
- **Nesting didn't separate them, because the parents were rarely found at all.** No arm, in 15 interviews, asked what
  happens to money left in an account being closed (N2's parent), so none of its children came up. N1's parent
  (approval over £100) came up in 1 G run and 3 S runs, each time because the agent *recommended* "no maximum amount"
  and was corrected. Once the parent was known, both G and S asked about the children; S once built its own reading of
  "needs approving" instead. The test of following a design tree never really happened: the bottleneck was finding
  the branch.
- **One rule was never found by anyone.** No run in any arm asked whether savings accounts' limits can change. The
  independent brief check had flagged it as unreasonable to expect; the result agrees.
- **Three questions went a long way on simple tickets.** K met 19 of 25 on the few-unknown tickets with about 80 words
  to read. It fell behind with four unknowns on one ticket (6 of 20) and met nothing on the nested ones.
- **Grilling did worse on GRL's own tickets this time.** On S1, S2, L1 and L2, G met 21 of 25 here against 15 of 15 in
  GRL; S1's rule (support may only add internal notes) was raised in only 2 of 5 G runs. The skill's coverage varies
  run to run more than GRL's three runs per cell suggested.
- **K asked open questions, without recommendations,** so it never needed correcting; its rules came from the
  developer's answers. G and S mostly recommended an answer, and the gain came from the 26 (G) and 34 (S) corrections.

## 7. What this might mean in practice

### Impact

On these tickets, a two-sentence prompt did what the grilling skill did. Both recovered most rules when the ticket's
gaps were the kind an agent thinks to ask about (who may do what, what gets recorded), for about half the reading with
the prompt. Neither found rules the agent had no reason to suspect, and nesting was not where the skill pulled ahead:
both missed the parent rules about as often.

The practical line is not "skill or prompt" but "will the agent think to ask about this at all?". Where it would,
asking for a list of open decisions with recommendations is enough. Where it wouldn't (money left in an account,
savings accounts being different), no interview format helped; the rule has to be in the ticket, the code or the docs.

### Configuration recommendations

| Recommendation | Why | Strength |
| --- | --- | --- |
| Before an agent builds from a ticket, ask it to list the open decisions with recommended answers and wait | Matched grilling (35 against 34 of 75) at half the reading | Strong on flat tickets: pre-registered non-inferiority; descriptive overall |
| Read each recommendation; correct the wrong ones | Every rule recovered by G and S came from a question; most from a corrected recommendation | Descriptive (consistent with GRL) |
| For quick tickets with one or two unknowns, "at most three questions" is a cheap option | 19 of 25 against 21 of 25, with about 80 words to read | Descriptive |
| Don't cap the questions on tickets with many unknowns | K met 6 of 20 on M1 against 10 (G) and 9 (S) | Descriptive, one ticket |
| Write down the rules an agent wouldn't think to ask about (special account types, what happens to money) | No arm found N2's parent or M1's savings rule in any run | Descriptive |
| Installing the grilling skill is optional, not required | No measurable advantage over the prompt here, and it costs more reading and time | Descriptive; one model |

### Risks this exposes

- **An interview feels thorough without being complete.** G asked 10–13 questions per run and still missed the
  nested parent rule in 9 of its 10 nested runs. The developer can't tell from the length of the interview what wasn't asked.
- **The gaps are shared.** The arms found the same rules and missed the same ones: all three mostly missed that
  support may only add internal notes (S1), and none found the savings rule or N2's parent. Relying on any interview
  for rules like those is relying on luck.

## 8. What the experiment does not prove

- **The developer was Claude following a fixed brief, not a real person.** It knew every answer and corrected every
  wrong recommendation. This measures how well each format extracts what the developer knows, not how a real team
  arrives at requirements.
- **Nesting was hardly tested.** The parents were found in 4 of 30 nested interviews, so hypothesis 2 compared formats
  that mostly never reached the nested part. A ticket whose parent rule an agent reliably raises would test nesting
  properly.
- **One wording each for S and K, one model, one repository, seven tickets, 15 rules, 5 runs per cell.**
  Non-inferiority held with little room (lower bound −0.13 against a −0.15 margin).
- **I wrote the tickets and rules.** Two rules (M1 savings, N2's parent) were found by nobody; with them removed, every
  format scores higher, but the comparison between formats doesn't change.

## 9. What I'd test next

- **Nested tickets whose parent rule is easy to ask about**, so the follow-up questions are actually tested.
- **The same prompts on a second model** (and Claude), to see whether the prompt matching the skill is a property of
  Luna.
- **A real developer** answering the same briefs, including wrong and uncertain answers.
- **A prompt that asks the agent to check its open decisions against a short list of usual gaps** (money, account
  types, audit trail), to see whether a checklist finds what interviews miss.

## 10. How to reproduce the results

```
scripts/check_references.sh                 # every reference meets every requirement
GVP_WORK=... scripts/pilot.sh              # ticket-only pilot
GVP_WORK=... scripts/main.sh               # 35 ticket-only runs
python3 -I scripts/relay.py setup|start|reply|list   # the 105 interviews, anonymous IDs
python3 -I scripts/run.py grade <run>; python3 -I scripts/audit.py <runs>
python3 -I scripts/analyse.py              # tables and results/summary.json
scripts/export.sh                           # copies runs into results/, checks for personal data
```

## 11. What changed from the design

All in the README's amendment log: the brief-check changes and the pilot (before the main run), and during the main run
the developer replies that needed a judgement call. Nothing changed in the hypotheses, tickets, tests or analysis
after the main run started.

**Correction (1 November 2026, after the site page went live):** section 7 said grilling "missed every nested parent".
One G run did raise N1's parent; the text now says it missed the parent in 9 of its 10 nested runs. No number or
hypothesis changed.
