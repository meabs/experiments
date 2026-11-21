# Will agents build a working society without being told to cooperate? (SOC)

**Status:** design, 2026-11-20; written before model calls. Local exploratory
simulation commissioned by Garry; an AI agent designed and implemented it.

## 1. Question

Will eight residents with private objectives spontaneously trade, support public
buildings and form repeated relationships? Does charging for messages change this?
Can one especially competitive resident gain at others' expense?

## 2. Why it is worth testing

Earlier experiments here assigned teams and tested handoffs or herding. This lets
agents choose relationships. Prior art includes [Shall We Team Up](https://arxiv.org/abs/2402.12327)
and [Cooperate or Collapse](https://arxiv.org/abs/2404.16698). This is an inspectable
local simulation, not a claim to have invented agent societies or modelled people.

## 3. What is being changed: the arms

| Town | Messages | Everything else |
| --- | --- | --- |
| Brook | free | identical initial population, private goals, resources, recipes and weather |
| Flint | one coin per delivered message | same as Brook |

Eight separate residents per town, all using `huihui_ai/Qwen3.8-abliterated:latest`
through local Ollama. Model digest and runtime version are recorded before runs.
One resident (Rook) is more aggressive: competitive, hard bargaining, concerned
with becoming the richest; never instructed to lie or harm anyone. The other
seven have varied temperaments. These profiles are fixed in both towns, not a
separate causal test. Nobody is instructed to cooperate or assigned a leader.
The two towns cannot communicate. Each resident sees their own inventory, goal,
memory, addressed messages, public offers and events, but not other inventories,
private goals or memories. Observer access is broader and explicitly labelled.

**Rules version 2 (2026-11-20, owner's request after run 1).** Run 1 (v1 rules, kept in
`results/run1-v1-rules/`, stopped on day 33) lost four of eight residents in each town to starvation:
the forester, mason and smith gathered wood and stone for their private goals and never food, while the
farmers held a food surplus and nobody traded or gave food. v2 changes three things at once, so the
effect of any one cannot be separated:

1. **Self-preservation as the first rule.** The prompt opens with "RULE 1, ABOVE EVERYTHING ELSE: STAY
   ALIVE"; each resident sees a daily `survival` line (food days left, a LOW FOOD warning at 3 or less, a
   STARVING warning at 0); a dead resident's goal score is zero. The engine rules for hunger are unchanged.
2. **A police force and an army in every town**, each already at level 1 (maximum 3), upgraded by the
   existing `contribute` action (police 6 wood + 4 stone + 1 tool per level; army 8 wood + 6 stone + 2 tools).
   They are institutions run by the engine, not extra residents.
   - **Army:** raiders reach each town at the end of every 6th day and take 20% of every living resident's
     food at level 1, 10% at level 2, none at level 3 (rounded down).
   - **Police:** a new action `take` (target, resource, amount 1 to 3) is allowed. It works with chance 50%,
     30%, 15% at police level 1, 2, 3. A failed attempt costs 2 coins (to the town). A successful one is
     caught with chance 40%, 60%, 80%: nothing is taken and the thief pays the victim 3 coins. Otherwise the
     thief keeps the goods. Outcomes come from a seeded draw by (seed, day, town, actor), so they are
     replayable; the independent verifier recomputes each one.
3. Nothing else changes: same residents, goals, recipes, weather, messaging fees, scheduler and model.

**Rules version 2.1 (2026-11-20, after reading run 1's logs).** Two additions, both made before any v2.1
model call:

1. **Interface fixes** found in the run 1 logs (see the amendment log): a `last_result` line tells each
   resident whether their previous action happened or was REJECTED; rejection messages for `contribute`
   name the missing field and give an example; the prompt lists the exact JSON for every action and warns
   that notes are written before the engine confirms an action.
2. **Technology.** Residents may `invent` (a name they choose, up to 40 characters, and one effect from a
   fixed list) for 4 wood + 4 stone + 2 tools, at most two inventions each and one per effect. Effects,
   all checkable by the engine and the independent verifier: `seed_selection` (+1 food when gathering
   food), `sharp_tools` (+1 wood or stone when gathering), `efficient_forge` (+1 tool when crafting),
   `food_preservation` (no meal needed on days divisible by 3), `granary` (raiders cannot take your
   food), `lockbox` (nobody can `take` your goods). The inventor benefits; `teach` (target, tech_id) shares
   it for free and the teacher keeps it. Inventions are public. This is design in the sense of choosing
   what to build and what to share, not free-form engineering: the engine cannot score a free-text design,
   so every effect comes from a fixed catalogue.

## 4. The fixtures

The Python engine creates a town from a seed. Residents gather food, wood or
stone; craft tools; build/upgrade private homes; contribute to a farm, well,
market, storehouse and clinic; make bilateral offers; accept/cancel offers;
give resources; and send public or private messages. One economic action plus
one message per turn. Agents choose actual structured actions: prose changes
nothing. All own-inventory debits are checked, offers settle atomically and
expired offers cannot execute. No shell, file, external service or network tool
is exposed to residents. Food is consumed at sunset; hunger costs health; rest
with food restores health. A resident at zero health is inactive permanently.
Recipes and benefits are visible to residents. Homes and public buildings have
finite upgrade levels. Public projects can be replenished as later upgrades.

One round = one simulated day = one turn per living resident. Order is shuffled
by seed per day; paired towns have the same order and weather. Calls interleave
towns. Decisions are sequential, avoiding simultaneous local model contention.
Private memory is bounded, and public/inbox context is a rolling window. All
events and decisions remain in the observer's permanent records.

**Free checks:** deterministic self-tests exercise safe and invalid trades,
overspending, forged identities, negative/boolean amounts, resource accounting,
message privacy, town isolation, starvation, construction, and restart/replay.
An independent verifier reconstructs the final town from accepted events and
checks nonnegative holdings, coin conservation, trade conservation and production
and consumption accounting. Decisions, engine events, and state snapshots are
separate records; none is evidence of human-like intent.

**Pilot rule:** at least one complete paired day (16 decisions). Require >=75%
parseable model decisions and >=50% accepted economic actions, zero verifier
failures, no leaked private state in resident observations, and one scripted
successful trade and building self-test. Otherwise stop and fix before main.
Pilot is marked PILOT-ONLY. No pilot decisions carry into main. Any design
change after pilot is recorded below. Pilot need not show cooperation to pass.

## 5. Measures

Primary descriptive measure: completed bilateral trades per completed town-day.
Secondary: living residents, unmet food needs, individual goal scores, homes,
public building levels, resource production/consumption, gifts, messages,
repeated trade pairs, accepted/rejected actions, coin concentration and tokens.
Metrics are computed from engine state and ledger, never residents' claims.
The observer UI shows private information for inspection; residents do not.
Narrative alliances, leadership and dishonest statements are exploratory. Text
alone does not establish an alliance or intentional deception.

## 6. Hypotheses and analysis

Predictions fixed before the first model call (v1): H1 at least one voluntary trade in the free
town; H2 paid messaging reduces delivered messages per completed day; H3 at least
one public building completes without a cooperation instruction. These are
descriptive predictions, not confirmatory statistical tests. Added before any v2 model call, for the main run on
v2 rules (the v1 pilot and run 1 are history, not pooled): H3 is now "a completed public building other
than police or army"; H4 at least six of eight residents alive in each town on day 30 (run 1 had four);
H5 at least one theft attempt is made; H6 at least one police or army upgrade completes. Added before any v2.1 call: H7 at least one invention is made; H8 at least one technology is taught to another resident. H4 compares a
town with run 1's town under rules that changed three ways at once, so a survival difference cannot be
credited to self-preservation, police or army separately. Each town is one
dependent trajectory; days and residents are not independent repetitions.
Compare only common fully completed days. No p-values or confidence intervals
from two towns. Later inference would need independent paired seeds, ticket-
stratified permutation/bootstrap and Holm correction per repository procedure.
The aggressive resident's relative wealth is exploratory, confounded with role,
inventory and private goal. A later factorial experiment could isolate it.

## 7. Size, cost and time

Pilot: one paired day (16 model decisions), extend only for technical diagnosis.
Main: two towns x eight residents, up to 24 wall-clock hours, 10,000 days,
20,000 calls, 1 GiB of run data, whichever limit is first. Per call: 8,192 context
tokens, 384 output tokens, 180-second timeout, at most three transport attempts.
Stop gracefully with a STOP file; resumable durable checkpoints, no paid fallback.
Estimated provider cost **$0; ceiling $0**. Electricity is not measured; no dollar
claim is made about it. Download approximately 18 GB; runtime throughput is unknown
until pilot. Model download lives in Ollama storage, outside Git. Bounded context
and serial calls limit memory. Main gets a fresh 24-hour deadline after pilot;
restarts preserve that deadline. Stops are checked between and during calls.

## 8. Rounds

First run is a long-lived exploration and graphical observatory. The initial
population and engine are scripted; residents choose how the town develops.
Future work: independent worlds, disposition as a separate arm, held-out goals,
memory and communication rules. Do not change the running code mid-run.

## 9. Limits known in advance

One local model/quantization; abliteration is not evidence of more realistic
behaviour. Toy production, survival and incentives determine what is possible.
No inference about human societies or the real economy. Sequential turns and
bounded memory influence behaviour. Pilot and main are not pooled. Hardware
sleep pauses progress. No automatic report claims while main is in progress.
Publishing, pushing or merging requires the owner's separate instruction.

## 10. Amendment log

- 2026-11-20, before calls: owner requested a graphical observer and clarified
  that the more aggressive character should be within the town. Rook appears
  in both towns; no third town is introduced.
- 2026-11-20 (evening), before main: free checks re-run (self-test passed, 0 model calls; dry-run ok). Technical pilot, one paired day with `huihui_ai/Qwen3.8-abliterated:latest`: 16 of 16 decisions parsed and accepted, verifier passed, day 2 reached; gate passed (`results/pilot/`, PILOT-ONLY, excluded from main). Owner approved the main run. Design and scripts frozen (`results/design-freeze.json`); main started with `run.py --mode main --hours 24`, observer on 127.0.0.1:8765. The first launch attempt had only initialised an empty main database (0 events).
- 2026-11-20 (night), run 1 stopped by the owner on day 33 (517 decisions) after four of eight residents in
  each town starved; archived as `results/run1-v1-rules/` and `results/pilot-v1-rules/` with its freeze file,
  not pooled. Owner asked for self-preservation as a key rule and a police force and an army in each village.
  Engine, verifier, self-test, analysis and observer updated to rules v2 (see section 3); 15 self-test checks pass
  with no model calls, including seeded theft replay, forged-theft rejection and raid sizes. v1 records still
  verify under the new verifier. Hypotheses H3 to H6 revised or added above before any v2 model call. A new pilot
  and a new freeze follow before the main run.
- 2026-11-20 (night), log review of run 1 (362 decisions, 361 parsed) and of the v2.0 pilot, before any v2.1
  call. Findings that change how run 1 is read:
  - **Interface bug in `contribute`.** Eli, Gus and Fern were rejected 29 times for "project does not need that
    resource": they sent `contribute` without the `resource` field (or `target:"stone"` instead), and the message
    was misleading. Their own notes say "Contributed 4 stone to clinic", so they believed it worked and repeated
    it. Run 1's "no public building completed" is therefore partly an interface artefact, not only a failure to
    cooperate. Fixed in v2.1 (clear rejection text, action examples, `last_result`).
  - **Notes record intended results.** Memory is written in the same reply as the action, before the engine
    confirms it, so notes stated trades and crafts that were rejected (Eli accepted an offer the other party could
    not pay; Dara crafted with no wood, 7 rejections). Fixed by the prompt warning and `last_result`.
  - **Starvation.** Bram, Cleo, Dara and Gus never gathered food (0, 0, 2, 2 units in 11 to 18 days) and died when
    their starting food ran out; farmers held 48 to 91 food; three trades and no gifts in 517 decisions.
  - **Rook.** Priced as an aggressive merchant: repeated the same 15-coin offer four times with no buyer and no price
    change; offered a tool, not food, to Dara at 2 health for 6 coins. This is the intended disposition, not a defect.
  - **Run quality.** One unparseable reply in 362 (0.3%); mean 10.9 s a call; verifier passed on every check.
  The v2.0 pilot (16 of 16 decisions accepted, no rejections) is archived as `results/pilot-v2.0/`, not pooled.
  Technology (section 3) added; H7 and H8 added. Engine, verifier, self-test (22 checks pass, no model calls),
  observer and analysis updated; run 1 records still verify. A v2.1 pilot, a new freeze and the main run follow.
- 2026-11-20 (night), two more fixes found by the v2.1 pilot, before the main run. (1) Context: the prompt had grown
  from about 1,500 to 1,900 tokens at the start and about 2,900 after one day, against a 4,096-token window that also
  holds the reply; run 1's prompts had grown by about 1,700 over the game, so v2.1 would have crept to the limit, where
  Ollama silently drops the oldest text (the rules). The window is now 8,192 (`run.py`; provenance records it).
  (2) Schema: the pilot still had residents sending `contribute` without `resource` (4 rejections in 16 decisions). A
  probe of 10 calls on the same prompts found 0 of 5 contribute attempts carried `resource` under the flat action
  schema (the model filled unrelated fields: a contribute with `name`, `effect` and `tech_id`) and 5 of 5 under a
  per-action schema. This was the root cause of run 1's 29 failed contributions, not only the wording. The schema now
  has one exact form per action kind (required fields mandatory, no extra fields); the engine and the independent
  verifier still validate every action themselves. The v2.1 pilot with the flat schema is archived as
  `results/pilot-v2.1a-flat-schema/`; a new pilot follows.
- 2026-11-20 (night), v2.1 pilot with the per-action schema and 8,192 context: 16 of 16 decisions parsed, 15 accepted (the one rejection was a legitimate home-upgrade shortfall), 2 contributions accepted, verifier and self-test passed, prompt peaked near 2,800 tokens; gate passed (`results/pilot/`, PILOT-ONLY, excluded from main). Owner's earlier approval of a 24-hour run applied. Design and scripts frozen (`results/design-freeze.json`); main started with `run.py --mode main --hours 24` on rules v2.1, observer on 127.0.0.1:8765 and a read-only LAN view (not published). Run 1 (v1 rules), the v2.0 pilot and the flat-schema v2.1 pilot are archived and not pooled.
- 2026-11-21, main run (v2.1 rules) stopped early by the agent on the owner's instruction to "review to see if we are
  learning anything or we stop". Stop rule applied at day 229 (228 complete days, 3,658 decisions, about 11.9 hours of
  model time of the 24 allowed): all 16 residents alive at full health for many days, contributions fell from 41 to 5
  per 50 days, trades from 10 to 0, no new kind of event after day 199, and food hoards of 755 to 1,059 in the farmers'
  inventories. This rule was written after seeing the data, so it is a judgement, not a pre-registered stopping rule.
  Data kept in full; verifier passes over all 8,002 events. Hypothesis outcomes are in `results/main/analysis.json`
  and REPORT.md; no p-values, as in section 6.
