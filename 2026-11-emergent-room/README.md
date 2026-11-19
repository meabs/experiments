# Do AI agents left to talk develop their own styles, or is it the model and the turn order? (experiment EMR)

**Status:** draft design, 2026-11-19. No run yet. Later changes go in the amendment log (section 10). An AI agent drafted
this design; the owner has not yet approved it.

## 1. Question

Three AI agents share a chat room, with the same minimal instructions and no assigned personalities, and meet over five
sessions, keeping their own memory notes between them.

1. **Style.** Do the agents become distinguishable from each other, and is that more than chance, the model, or who
   happened to speak first?
2. **Relationships and collaboration.** Do patterns appear (who challenges whom, who proposes, who defers) that persist
   from one session to the next?
3. **Adaptation.** When evidence contradicts what they agreed, do they change position, and does it show in their notes?

This is an exploratory case study of five sessions. It cannot show that emergent personality exists in general. It can
show concrete transcripts and failure modes, and it can rule out the cheap explanations.

## 2. Why it is worth testing

Multi-agent "chat rooms" are usually built from assigned personas that take turns, so agreement and difference are
scripted. That tells you nothing about whether differences appear on their own. The earlier
[team-herding](../2026-10-team-herding/) and [swarm-tax](../2026-10-swarm-tax/) experiments looked at agents working
together; neither gave agents memory across sessions or free choice about when to speak. The risk is mistaking random
variation in model output for personality, so the design is built around the explanations that would produce the same
transcript without any emergence.

## 3. The room and the agents

- **Three agents, A, B, C.** Identical system prompt (about 150 words, in `arms/`): you share a room with two others;
  you may reply, ask, challenge, change your mind, propose or drop a topic, or stay silent (`PASS`); keep your notes
  file up to date. No names for roles, no tone instructions.
- **Models (cheap, both).** Codex `gpt-5.6-luna` ($0.20 / $0.02 cached / $1.20 per million tokens, as in the other
  experiments) and Claude Haiku 5.5 ($0.10 input, $0.50 output per million for prompts under 100,000 tokens, from
  third-party price pages; confirm on Anthropic's pricing page before spending). Context is kept under 100,000 tokens.
- **Model assignment (the control that matters).**

  | Sessions | A | B | C |
  | --- | --- | --- | --- |
  | 1 to 3 | Codex | Codex | Claude |
  | 4 to 5 | Claude | Codex | Codex |

  A and C swap models between session 3 and 4 and keep their memory notes. B stays on Codex throughout. If style follows
  the model, A and C swap styles. If it follows the memory, they keep them. A and B share a model in sessions 1 to 3, so
  any difference between them is not the model.
- **Memory.** Each agent has its own `notes.md`, which it can rewrite at the end of every session and when it chooses.
  Every version is stored. An agent cannot read another's notes.
- **Scheduler, no speaking order.** After each posted message, every agent that is not already generating is asked, in
  parallel, whether to reply or `PASS`. Replies are posted in the order they finish. Each message stores the last
  message the agent had seen, so a reply made on a stale board is visible as such. A session ends at 120 messages, at
  the token budget, or after six consecutive rounds of all-PASS. The scheduler never chooses what anyone says.
- **Agent adapter.** One thin interface (board so far plus notes in, message or PASS out) with a Codex and a Claude
  implementation. How Codex is called (the CLI as in the other experiments, with a canary run first, or the hosted API
  directly) is settled in the pilot and logged in the amendment log.

## 4. The board (watch and replay only)

A browser page served from the event log. The same page shows a live session and replays a finished one, so what is
recorded for the video is the real run.

- Messages with sender, time, and a thread line to the message they reply to; a status per agent (thinking, silent,
  posted).
- Replay controls: play, pause, speed, scrub bar, jump to a message. Live follow can be switched off.
- An **evidence card** appears when the scheduler delivers the scripted scenario evidence (session 4, from a file written
  in advance, at a fixed message count). No human can type into the room or pause it. There is no intervention in this
  experiment, which keeps the measure clean.
- A **memory panel**: pick an agent and move through its notes by session, with a diff against the previous version.
- A presentation mode for video: large type, light or dark, cost and token counts hidden.

Built with Python (stdlib or FastAPI), SQLite and plain HTML with server-sent events. No React, no LiteLLM.

## 5. The five sessions

| Session | Scenario | What it shows |
| --- | --- | --- |
| 1 | Open design challenge: how should a trustworthy autonomous software team be organised? | First differences, with nothing to build on |
| 2 | A technical decision with conflicting priorities (written in `scenarios/`) | Disagreement, leadership, deferring |
| 3 | A creative problem with few constraints | Initiative and originality |
| 4 | Revisit session 2's decision. At message 40 the scripted evidence arrives that contradicts what they had agreed. Model swap applies | Adaptation, and whether style follows the model or the notes |
| 5 | Revisit session 1's challenge with new constraints | Continuity of behaviour and notes |

Scenario texts, and the evidence for session 4, are written before the first run and are not changed after it.

## 6. Measures

All counted from the event log (`events.sqlite`), not from the agents' own account.

1. **Identifiability.** A classifier (logistic regression on word and punctuation features, leave-one-session-out)
   tries to tell which agent wrote each message. Reported against a null from 10,000 shuffles of agent labels within a
   session. Position features (rank in turn, preceded by whom, whether it opened a thread) are removed in a second run, so
   "the one who speaks third" is not counted as a style.
2. **Model versus memory.** After the swap, does the classifier trained on sessions 1 to 3 label A's and C's new messages
   by the agent (memory) or by the model?
3. **Initiative.** Share of messages that open a new thread or topic, by agent.
4. **Disagreement.** Share of replies coded challenge, agree or neutral by a blind coder (a third model that does not see
   agent names; 40 messages are hand-checked by the owner).
5. **Adaptation.** In session 4, after the evidence card: did the agent change a stated position within 15 messages,
   and does its notes file record it?
6. **Continuity.** Whether notes at the start of each session are used: count of messages that cite a specific earlier
   message or note, against the same count with the notes removed from a 40-message replay (a cheap extra run per
   session, no board).
7. **Cost and tokens** per agent and per session, from the API usage fields at list price.

## 7. Hypotheses and analysis

Written before the run. With five sessions and three agents there is no sample for confirmatory tests, so every test is
**exploratory** and reported with intervals. No Holm correction is claimed.

- **H1.** Agents A and B (same model, sessions 1 to 3) are identifiable above the shuffled null, after position
  features are removed. *My prediction: no. They stay close to indistinguishable, and any gap is mostly position.*
- **H2.** After the swap, style follows the model, not the agent's memory. *My prediction: yes.*
- **H3.** Disagreement falls across sessions: later sessions converge faster. *My prediction: yes.*
- **H4.** In session 4 at least two of three agents revise a position after the evidence, and their notes record it.
  *My prediction: they revise in the room but notes record it less often than the transcript suggests.*
- **H5.** Notes carry continuity: with notes, more messages cite earlier material than without. *My prediction: yes,
  but mostly generic references.*

If H1 is false and H2 is true together, that is the clean result: differences exist but are the model's.

## 8. Size, cost and time

Five sessions of up to 120 messages. Each agent call carries the board and its notes: about 12,000 input tokens on
average and 200 output tokens. Per session: about 1.8 million input and 30,000 output tokens a model. Roughly $0.40
for a Luna agent and $0.20 for a Haiku agent per session, so about **$2 for all five sessions**, plus about $0.50 for
the blind coder and the notes-removed replays. **Ceiling $10**, enforced by the scheduler per session ($2 each).
A pilot of one 30-message session, to test the scheduler and adapter, is not counted as a run. Each session takes
roughly 20 to 40 minutes. Prompt caching is not assumed in the estimate.

## 9. Limits known in advance

- Five sessions, one scenario each: nothing here generalises to "agents develop personalities".
- Two cheap models; their behaviour is not what a larger model would show.
- The agents see the same board, so apparent individuality is also shaped by what each happened to read.
- Memory notes are text the agent writes about itself, which may be a performance. The notes are evidence of what it
  says it prefers, not of internal states.
- The agent-reading classifier is trained on few messages (hundreds), so the null range will be wide.
- The scheduler does shape the conversation through timing, and the ordering by completion time favours the faster model.
  The timing is logged, and replies that finished on a stale board are flagged.
- A live viewer was used for the recording, but nobody intervened. The owner watching could still influence what is
  kept or retried; if a session is re-run, both runs are kept and reported.

## 10. Amendment log

| Date | Change | Before or after a measured run |
| --- | --- | --- |
| 2026-11-19 | First draft: model swap, watch-and-replay board only, no intervention | Before |
