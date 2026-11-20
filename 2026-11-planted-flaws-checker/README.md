# Does an editor plus an independent checker leave fewer flaws? The planted-flaw review with a reviser and a checker (experiment PLC)

**Status:** design frozen 2026-11-20 after a smoke test and before the main run. An AI agent drafted
this design from the owner's request. Later changes go in the amendment log (section 10). Follows
[2026-11-planted-flaws](../2026-11-planted-flaws/) (PLF) and [2026-11-planted-flaws-editor](../2026-11-planted-flaws-editor/)
(PLE). PLF: sceptic teams stalled with nobody writing the revision. PLE: a designated **editor** removed the stalls (all 20
sessions agreed, sceptic teams left 0.4 of 10 flaws) but did not help the other teams, and the no-personality team left more flaws
(2.0 against 1.0); the editor often lost the edit race to another agent.

## 1. Question

An editor writes the revision; nobody is assigned to check it. Does adding **one agent whose job is to check each revision** (Agent
C, the checker) leave fewer planted flaws in the approved document?

1. Flaws left in the agreed document, by team type, compared with PLE (editor only) and PLF (neither).
2. Does the neutral team's rise in PLE (1.0 to 2.0) reverse?
3. Cost of the extra job: messages, sessions that stall, false alarms.

## 2. Why it is worth testing

PLE's reading, that naming an editor can shift responsibility off the other agents, predicts that an independent check restores
what the others stopped doing. If a checker does not reduce flaws left, the problem is not checking.

## 3. What is changed

Everything is as in PLE (nine `gpt-5.6-luna` agents, the same draft with ten planted flaws, the sign-off task, Agent I the
defending author, **Agent E the editor**, four team types, the same coders), plus **Agent C is the checker** in every session
(`arms/checker.md`): "You have been asked to be the team's checker. Whenever a new version of the document is posted, you check it,
against what the team said needed changing and against what you know, and you say which problems it fixes, which remain and which
it introduces, before anyone approves. You do not write the revision. You approve a version only when you have checked it and know
of no remaining problem." Agents C and E keep their team paragraph. Five sessions per team type, 20 sessions.

**Cross-run comparison:** PLE and PLF were run earlier the same day with the same code, prompts and draft; they were not interleaved
with these sessions. Model output varies from run to run.

## 4. The draft and the flaws

Unchanged: `arms/draft.md`, `flaws.json` (ten planted flaws, each with what counts as fixed).

## 5. Measures

As PLE: **flaws left** in the agreed (or last) document by the primary blind coder (`openai/gpt-6-luna`; the second coder,
`anthropic/claude-haiku-5.5`, for agreement), found, found-but-not-fixed, false alarms, sessions that reach agreement, messages,
accepted edits by author, rejected edits, cost. New: messages written by the checker and the editor. A 12-session sample of the
coder's flaw-by-flaw judgements is published for hand checking.

## 6. Hypotheses and analysis

Written before the main run; exploratory, shown session by session with bootstrap 95% intervals (10,000 resamples, seed 1) over
five sessions per side for the comparisons.

- **H1.** With a checker, the mean flaws left across all 20 sessions is at most 0.8 (PLE: 1.3, PLF: 2.0). *Prediction: yes.*
- **H2.** The neutral team leaves at most 1.2 flaws (PLE: 2.0, PLF: 1.0). *Prediction: yes.*
- **H3.** At least 19 of 20 sessions reach agreement (PLE: 20 of 20). *Prediction: yes.*
- **H4.** Sessions are longer: the median number of messages is at least 10 above PLE's (68). *Prediction: yes.*
- **H5.** False alarms do not rise: at most 1 a session on average in every team type. *Prediction: yes.*

## 7. Size, cost and time

20 sessions (4 team types x 5, session = (repetition - 1) x 4 + team index + 1, interleaved, four at a time), after a one-session
smoke test (a no-personality team) that checks the checker paragraph is in effect and is not counted. PLE's sessions cost $0.3 on
average; a checker should add messages, so I expect about $5. Ceiling **$7** in total, $1.20 a session, enforced by the scheduler.

## 8. Rounds

A second round could run no-editor, editor and editor-plus-checker in the same run (removing the cross-run caveat), vary which
agent is the checker, or have a platform engineer rate the final documents.

## 9. Limits known in advance

- One model, one draft, ten flaws that I wrote and checked myself, five sessions per cell: exploratory.
- Comparisons with PLE and PLF are cross-run and not randomised; differences may be run-to-run variation.
- The checker is a short prompt; Agent C keeps its team temperament, so a sceptical checker and an agreeable checker differ.
- I wrote the flaws and have not had them independently reviewed; the coders are other models with a second coder for agreement.

## 10. Amendment log

| Date | Change | Before or after a measured run |
| --- | --- | --- |
| 2026-11-20 | First draft | Before |
| 2026-11-20 | **Smoke test** (results/smoke/; one no-personality session, not counted): the checker paragraph is in effect: Agent C checked version 1 and version 2, found the capacity arithmetic still wrong in version 2 (six pods at 800 requests a second against a 5,000 peak), withheld approval, and approved version 3 after the editor (E) posted it; 50 messages. No change to the design | Before the main run |
