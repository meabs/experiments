# Does giving a team an editor stop sceptics stalling? The planted-flaw review with a designated reviser (experiment PLE)

**Status:** design frozen 2026-11-20 before the main run (a one-session smoke test is allowed, section 7). An AI agent drafted this
design from the owner's request. Later changes go in the amendment log (section 10). Follows
[2026-11-planted-flaws](../2026-11-planted-flaws/) (PLF), whose main finding was that every team found most of ten planted flaws,
agreeable teams approved more of them, and two of five sceptic teams refused to approve the draft but **nobody wrote the
revision**, so it went through unchanged.

## 1. Question

PLF suggested that the sceptic teams' stalls came from nobody owning the revision. This tests it directly: in every team,
**one agent (Agent E) has the job of writing the revision**.

1. Do the stalls go away: do sceptic (and all) teams reach an agreed version?
2. What is left in the document: does the editor change the number of flaws left, and does the agreeable team's gap persist?
3. What does the editor do: how much of the document change comes from the editor?

## 2. Why it is worth testing

PLF's lesson, "give someone the job of writing the revision", is my interpretation of two stalled sessions out of five. It is a
cheap, concrete claim that a controlled change can confirm or refute. If the stalls persist with an editor, the cause is not
missing ownership.

## 3. What is changed

Everything is as in PLF: nine `gpt-5.6-luna` agents (A to I), the same draft (`arms/draft.md`), ten flaws (`flaws.json`), task
(`arms/task.md`, a sign-off), room rules (`arms/base.md`), compare-and-swap editing, four team types (none, Belbin roles, all
sceptics, all agreeable; the paragraphs are unchanged), Agent I the author who defends the draft, five sessions per team type, the
same coders. **One change:** in every session **Agent E** has an extra paragraph (`arms/editor.md`): "You have been asked to be the
team's editor. Your job is to write the revised document: once the team has said what needs changing, you post the complete revised
document with those changes made ... You are not the one who decides what is wrong, and you are not the author of the draft."
Agent E also keeps its team paragraph (a sceptic or agreeable temperament, or a Belbin role).

The comparison for each team type is PLF's five sessions of that type (no editor). **That is a cross-run comparison:** the PLF
sessions were run earlier on the same day with the same code, prompts and draft, not interleaved with these. Model output varies
from run to run, so differences are suggestive, not clean.

## 4. The draft and the flaws

Unchanged from PLF: ten planted flaws (see `flaws.json`) in `arms/draft.md`; the agreed (or, if none, the last) document is judged
against each flaw's `fixed_if` criterion.

## 5. Measures

1. **Reached agreement.** Sessions that ended with all nine approving, out of 20 (PLF: 18 of 20).
2. **Flaws left** in the agreed (or last) document, out of 10, by the primary blind coder (`openai/gpt-6-luna`); the second coder
   (`anthropic/claude-haiku-5.5`) for agreement. Per session, by team type, with the PLF values beside them.
3. **Found** (said to be wrong in discussion), **found but not fixed**, **false alarms**, as in PLF.
4. **The editor's share:** accepted document edits written by Agent E, as a share of all accepted edits; sessions where nobody
   posted a revision.
5. Process: messages, versions, rejected edits, cost.
6. A 12-session sample of the primary coder's flaw-by-flaw judgements is published for hand checking.

## 6. Hypotheses and analysis

Written before the main run. Five sessions per team type: exploratory, shown session by session; differences from PLF carry a
bootstrap 95% interval (10,000 resamples, seed 1) over five sessions per side.

- **H1.** With an editor, no sceptic session stalls: all five reach agreement (PLF: three of five), and the sceptic teams leave
  at most 1 flaw on average (PLF: 4.0). *Prediction: yes.*
- **H2.** The agreeable gap shrinks but does not close: agreeable teams still leave at least 0.5 more flaws than no-personality
  teams. *Prediction: yes.*
- **H3.** At most 1 of the 20 sessions ends without agreement (PLF: 2 of 20). *Prediction: yes.*
- **H4.** The editor writes at least 70% of the accepted edits. *Prediction: yes.*
- **H5.** Across all teams the mean number of flaws left is at most 1.5 (PLF: 2.0). *Prediction: yes.*

## 7. Size, cost and time

20 sessions (4 team types x 5, session = (repetition - 1) x 4 + team index + 1, interleaved, four at a time), after a one-session
smoke test (a SCEPTIC team) that checks the editor paragraph works and is not counted. PLF's sessions cost $0.07 to $0.32 each; I
expect about $3. Ceiling **$6** in total, $1.20 a session, enforced by the scheduler.

## 8. Rounds

A second round could make approval depend on a closed list of objections, vary which agent is the editor, give the editor no
temperament, or run the no-editor and editor conditions in the same run to remove the cross-run caveat.

## 9. Limits known in advance

- One model, one draft, ten flaws that I wrote and checked myself, five sessions per cell; exploratory only.
- The no-editor comparison is PLF, run earlier; the comparison is not randomised, and a difference could be run-to-run variation.
- The editor paragraph tells Agent E to write the revision; it tests what the model does when given that job, not whether a human
  team would behave the same.
- Agent E also carries its team temperament, so an agreeable editor and a sceptical editor are different editors.
- The coders are other models, with one coder checked by a second, not by a person; a sample is published.

## 10. Amendment log

| Date | Change | Before or after a measured run |
| --- | --- | --- |
| 2026-11-20 | First draft | Before |
