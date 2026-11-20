# Does a harder design task, and two forceful agents, change how a Belbin team writes a design? GKE with Cloud SQL and change data capture to BigQuery (experiment BLC)

**Status:** design frozen 2026-11-20 before any run of this experiment. An AI agent drafted it from the owner's request.
Later changes go in the amendment log (section 10). Follows [2026-11-belbin-gke](../2026-11-belbin-gke/) (BLB).

## 1. Question

BLB gave nine agents the nine [Belbin team roles](https://www.belbin.com/about/belbin-team-roles) as personalities and had them
write a highly available GKE design. The roles barely showed, the rooms agreed quickly (three of four on version 1), and
the checklist scored 23 of 24 everywhere. This experiment makes two changes the owner asked for:

1. **A harder task:** the database is Cloud SQL (PostgreSQL) with change data capture (CDC) into BigQuery within about five
   minutes, without endangering the primary, through failover, with a regional-recovery story and personal data.
2. **Two agents given a forceful, opinionated paragraph** in their system prompt, on top of their Belbin role.

Questions: do the two forceful agents show, and do they pull the room (talk, edits, positions in the document)? Does a
forceful minority change how the team works (challenge, revisions, time to agree)? Does it change the document?

## 2. Why it is worth testing

In BLB nobody revised version 1 although several asked for changes: a polite room approved quickly. People sometimes
think a strong voice or two improves a design by forcing debate; others think it just dominates. Agents given an opinionated
voice are a direct test of that, with the task hard enough that a checklist is less likely to saturate.

## 3. What is changed: the two conditions

| Condition | System prompt |
| --- | --- |
| BASE | shared room instructions (`arms/base.md`) plus each agent's Belbin paragraph (`arms/roles.json`), as in BLB |
| FORCEFUL | BASE, plus for agents **D and H only** the paragraph in `arms/forceful.md`: strong opinions argued forcefully, blunt, presses its position, does not give way without a compelling reason, "the ideas you attack, never the people" |

Held constant: nine agents A to I, `openai/gpt-5.6-luna` for all, through OpenRouter, low reasoning effort, temperature
1.0; the task (`arms/task.md`); one shared document with compare-and-swap edits; no speaking order; no memory between
sessions. In the second repetition roles are assigned to letters in reverse order, so D and H carry different Belbin roles
in the two repetitions (rep 1: Plant and Implementer; rep 2: Specialist and Teamworker). The forceful agents are
fixed by letter, chosen here before any run, not by role.

## 4. The task and the room

`arms/task.md` (GKE platform for a customer-facing web app, 99.95%, 5,000 requests a second, zone loss unattended, rehearsed
region recovery, eight engineers) plus: Cloud SQL (PostgreSQL) as the transactional database and CDC of every committed change
into BigQuery within about five minutes, without endangering the primary, working through failover, defined behaviour in a
regional recovery, and handling of ordering, duplicates, schema changes, the first backfill and personal data. It names the
topics to cover but not what to say about them. Room rules are as in BLB: `DOC:` replaces the document if based on the current
version, otherwise it is rejected with a notice; `AGREE vN` approves; the session ends when all nine agree, at 150 messages,
at a $2 budget or when the room goes quiet.

## 5. Measures

1. **Do the two show?** A blind coder (`openai/gpt-6-luna`), seeing anonymised speakers and the previous six messages, codes
   every message: stance (challenge, agree, neutral) and **forceful** (true when it insists, states a position as
   settled, dismisses an alternative, or demands a change). Share of forceful messages and of challenges for D and H against the
   other seven agents, by condition.
2. **Pull.** Share of messages by D and H (2 of 9 agents is 22% if everyone talks equally), document versions they author,
   and, per final document, the coder's count of the room's stated positions (up to five that the transcript shows were
   disputed) that the final document resolves in the favour of D or H.
3. **Process.** Messages, rejected edits, document versions, challenge share, whether and when all nine agree, per session.
4. **Document.** Blind coder scores the final document 0, 1 or 2 on 16 items: the 12 from BLB plus four for CDC: (13) the
   CDC mechanism and its load on the source database; (14) behaviour of the CDC through a database failover (resume, loss,
   duplicates); (15) BigQuery side: ingestion, de-duplication and merge, ordering, schema changes and backfill; (16)
   personal data in the analytics copy, and monitoring of the freshness target. A 2 needs a named mechanism and a setting or
   number. Total 0 to 32, word count, and the doubtful claims about GKE, Cloud SQL or BigQuery behaviour that the coder lists
   (unscored; for a person to check). **Pairwise judgement:** for each repetition the coder sees the BASE and FORCEFUL
   documents, in both orders, and says which is the better and more correct design; counts of wins.
5. Cost and tokens per session at list price.

## 6. Hypotheses and analysis

Written before any run. Two sessions per condition: all comparisons are **exploratory**, shown session by session.

- **H1.** The instruction works: in FORCEFUL sessions the coder marks at least twice the share of D and H's messages
  as forceful that it marks for the other seven agents; in BASE sessions D and H are not different from the rest.
  *Prediction: yes.*
- **H2.** The two take over: in FORCEFUL sessions D and H write more than 30% of the messages and author at least one
  document version. *Prediction: more than 30% yes; authoring a version less certain.*
- **H3.** A forceful minority produces more argument and more revision: FORCEFUL rooms have a higher challenge share, more
  messages and more document versions than BASE rooms. *Prediction: yes, though everyone still ends up agreeing.*
- **H4.** Better documents? The pairwise coder prefers the FORCEFUL document in at most half of the judgements, and the
  checklist totals differ by 3 or fewer out of 32. *Prediction: no gain.*

## 7. Size, cost and time

4 sessions (BASE, FORCEFUL, BASE reversed, FORCEFUL reversed), after one 30-message pilot of FORCEFUL that is not counted.
BLB's sessions cost $0.07 to $0.14 each at list price; this task is longer, so I expect $0.1 to $0.4 a session. Ceiling **$6**
in total, $2 a session, enforced by the scheduler. Paid from the owner's OpenRouter balance.

## 8. Rounds

A second round could give the forceful paragraph to roles chosen for fit (Shaper, Monitor Evaluator), change the model, or
add a human review of the documents for technical correctness.

## 9. Limits known in advance

- Four sessions, one model, one task: exploratory only. Two forceful agents, fixed by letter, not by role.
- The checklist measures coverage and specificity, not correctness. The doubtful claims are the coder's and a person has not
  verified them. The checklist and task were written by an AI agent.
- Forcefulness is an instruction in a prompt, so this tests what the model does when told to be forceful, not how people
  behave. The agents are told to attack ideas and not people, which limits how aggressive the transcript can be.
- The coder is another model and not hand-checked; a 40-message sample is published for checking.
- Compare-and-swap changes the dynamics of editing; there is no memory between sessions.

## 10. Amendment log

| Date | Change | Before or after a measured run |
| --- | --- | --- |
| 2026-11-20 | First draft | Before |
| 2026-11-20 | Pilot (FORCEFUL, 30-message cap, results/pilot/): worked, 30 messages, 2 document versions, 10 rejected edits, $0.098; D and H visibly more insistent ("mandatory", "still outstanding"). Not counted. No change to the design | Before the main run |
