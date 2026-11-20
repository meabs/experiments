# Do AI agents left to talk develop their own styles, or is it the model and the turn order? Report (experiment EMR)

**This experiment was designed and run with an AI agent** (Claude, working for me): it drafted the design, built the room
and board, ran the sessions and the analysis. I chose the question, the two models, and approved the design and the
spending.

2026-11-19 and 20. Design: [README.md](README.md), with every later change in its amendment log. Event log:
[results/events.sqlite](results/events.sqlite) (every message, pass, document and notes version). Numbers:
[results/analysis_style.json](results/analysis_style.json), [results/coded.json](results/coded.json). Board to replay any
session: `python3 -I scripts/board.py`.

## 1. What I wanted to find out

Three agents, one shared prompt with no personalities, five sessions with their own memory notes. Do they become
distinguishable, and is that the agent, or the model, or the turn order? A sixth session, added afterwards, asked them to
write and agree a design document.

## 2. What I predicted (written before the run)

H1 same-model agents are not distinguishable; H2 after swapping models between two agents, style follows the model;
H3 disagreement falls across sessions; H4 at least two of three agents revise a position after the contradicting evidence
and the notes record it, less often than the transcript suggests; H5 notes carry continuity.

## 3. How I tested it

Agents A, B, C in one room. `gpt-5.6-luna` and `claude-haiku-5.5` through OpenRouter, same system prompt, no speaking
order (every agent with unseen messages is asked in parallel). Sessions 1 to 3: A and B luna, C haiku. Sessions 4 and 5: A
haiku, B and C luna, with each agent keeping its notes. 286 messages in sessions 1 to 5; every session ended when the room
went quiet, none hit the cap. Analyses are **exploratory**: five sessions, one scenario each, no confirmatory tests.

## 4. What happened

**Same model, different agents: not distinguishable (H1).** A text-only classifier (tf-idf, nearest centroid, leave one
session out, agent names removed) tells A from B, both luna, in sessions 1 to 3 at balanced accuracy 0.52 against a
shuffled-label null of 0.50 (95th percentile 0.58; p = 0.36). It tells luna from haiku (B against C) at 0.96, so it can
detect a real difference. Dropping each agent's first three messages per session does not change either result.

**Style follows the model, not the agent's memory (H2).** Trained on sessions 1 to 3 and applied to 4 and 5, A's messages
(now haiku) are labelled as C (the old haiku agent) 21 of 22 times and as A once; C's messages (now luna) are labelled as
A or B 40 of 40 times and as C never. B against C, now both luna, drops to 0.48 (null 0.50). A against B, now haiku against
luna, rises to 0.89.

**Challenging belongs to haiku (exploratory, coded by a third model).** Share of messages coded "challenge":

| Agent | as luna | as haiku |
| --- | --- | --- |
| A | 1 of 69 | 7 of 22 |
| B (always luna) | 2 of 107 | - |
| C | 2 of 40 | 31 of 48 |

Agree dominates elsewhere: 79% to 92% of messages in each session. Across sessions the challenge share goes 19%, 18%, 14%,
6%, 16%, so it does not fall steadily (H3 not supported; session 4 is the low point).

**Adaptation after the evidence (H4): not supported.** The coder found no explicit change of position in the room for any
of the three agents after the session-4 evidence card. Agent C's notes record that the evidence shifted the decision to
"wait", although the coder found no revision in the room, so the room and the notes disagree on that one. The room had
already leaned towards waiting, which may leave nothing to revise.

**Continuity (H5): not tested.** No message in sessions 1 to 5 mentions "session" or refers back by name to earlier
sessions. The planned replay with notes removed was not run, so I cannot say whether the notes mattered.

**Session 6, design document (descriptive).** All three agents posted a complete document in the first round, each from an
empty start, so two of the three overwrote text they had not seen. They then converged on C's version (v3, about 1,000
words). A first agreed to the wrong version (v2), was told it was superseded, and then agreed v3. 12 messages, $0.018.

**Cost.** My token count at list price is $0.57 for everything in the log. OpenRouter's balance went from 149.457
(after the pilot) to 150.145, $0.69, which includes the blind coder (about $0.05) and two invalid attempts ($0.04).

## 5. What surprised me

How completely the behaviour moved with the model. The most vivid difference, challenging a peer, moved with it in both
directions after the swap, even though the agents carried their own notes. The shared system prompt did not stop haiku
agents being the room's sceptic. I expected some residue of the earlier role.

## 6. What this might mean in practice

If you give identical prompts to three agents and they sound different, check the models first. In this setup the
"personalities" were the models' defaults, and the agents did not adopt a role from their own history. Mixing models is
probably the cheapest way to get genuine disagreement in a room.

## 7. What the experiment does not prove

- Five sessions, one scenario each, two cheap models, one run each. No confirmatory test; every number is exploratory.
- The coded measures come from a single model's judgement, not hand-checked (a 40-message sample is provided to check).
  The "agree" category includes messages that endorse and then add, so the agree share is generous.
- The classifier is text only, on a few hundred messages; its null is wide. It says the two luna agents were not
  distinguishable by wording, not that nothing differed.
- Messages in parallel rounds are often written before newer ones land (53% to 78% per session), which shapes the
  conversation and favours the faster model.
- Notes are text the agent writes about itself. Agent C's final notes mislabel which topic session 4 was.
- The notes-removed replay (continuity) was not run.
- Session 6 was added after seeing sessions 1 to 5, with two invalid attempts kept and labelled (sessions 96 and 97).

## 8. What I'd test next

Two tests that would settle the open questions: a luna-only room and a haiku-only room, five sessions each, to separate
"room composition" from "model" (does a haiku-only room still produce a sceptic?), and a replay of each session's last
40 messages with and without the notes to measure continuity directly. Hand-checking the coded sample first.

## 9. How to reproduce the results

```sh
cd 2026-11-emergent-room
OPENROUTER_API_KEY=... scripts/run_all.sh                 # sessions 1-5
python3 -I scripts/room.py run --session 6 --adapter real --max-messages 150 --budget-usd 2 --db results/events.sqlite
python3 -I scripts/analyse_style.py
OPENROUTER_API_KEY=... python3 -I scripts/analyse_coded.py
python3 -I scripts/board.py                                # replay at http://127.0.0.1:8765
```

## 10. What changed from the design

See the amendment log in the README: OpenRouter in place of the Codex CLI; the room ends when it goes quiet; session 4
evidence timing; session 6 added after the run; two invalid session-6 attempts; the notes-removed replay not run; coder
details.
