# Does a harder design task, and two forceful agents, change how a Belbin team writes a design? GKE with Cloud SQL and change data capture to BigQuery. Report (experiment BLC)

**This experiment was designed and run with an AI agent** (Claude, working for me): it wrote the design, the room, the
analysis and this report. I asked for the harder task (Cloud SQL with change data capture into BigQuery) and for two of the
agents to be more aggressive and opinionated, and I paid for it from my OpenRouter credit. I have not reviewed the design
documents for technical correctness.

2026-11-20. Design: [README.md](README.md), frozen before the main run, with every later change in its amendment log. Follows
[2026-11-belbin-gke](../2026-11-belbin-gke/) (BLB). Event log: [results/events.sqlite](results/events.sqlite). Numbers:
[results/analysis.json](results/analysis.json). The four agreed documents: [results/docs/](results/docs/).

## 1. What I wanted to find out

Nine agents, each with a Belbin role, write one design document for a highly available GKE platform that now also needs
Cloud SQL (PostgreSQL) with change data capture (CDC) into BigQuery within about five minutes. In two of the four sessions,
agents D and H also get a paragraph telling them to hold strong opinions and argue forcefully. Do the two show, do they pull
the room, and does the document change?

## 2. What I predicted

H1 D and H are marked forceful at least twice as often as the other seven in FORCEFUL sessions. H2 they write more than 30%
of the messages and author a document version. H3 FORCEFUL rooms challenge more, take more messages and make more document
versions. H4 no better documents (checklist within 3 of 32, and the pairwise judge prefers the FORCEFUL one in at most half
of the judgements).

## 3. How I tested it

As BLB: nine `gpt-5.6-luna` agents through OpenRouter, a Belbin role each, one shared document with compare-and-swap edits, no
speaking order, a session ends when all nine agree. BASE sessions: roles only. FORCEFUL sessions: roles plus the forceful
paragraph for D and H ("the ideas you attack, never the people"). Two sessions per condition; in the second repetition the
roles are reversed across the letters, so D and H hold Plant and Implementer in rep 1 and Specialist and Teamworker in rep 2.
A blind coder (`openai/gpt-6-luna`) coded every message and scored the documents on a 16-item checklist fixed beforehand.
Exploratory: four sessions.

## 4. What happened

| Session | Condition | Messages | Versions (authors) | Rejected edits | Room challenge share | D+H share of messages | Checklist (of 32) | Words |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | BASE | 64 | 2 (H, H) | 5 | 29% (18 of 62) | 16% | 27 | 1,766 |
| 2 | FORCEFUL | 20 | 1 (A) | 5 | 16% (3 of 19) | 15% | 32 | 1,754 |
| 3 | BASE, roles reversed | 81 | 3 (E, H, B) | 9 | 24% (19 of 78) | 24% | 30 | 1,336 |
| 4 | FORCEFUL, roles reversed | 43 | 1 (I) | 6 | 36% (15 of 42) | 14% | 31 | 1,638 |

All four sessions ended with all nine agents agreeing. No session hit a cap. The sessions cost $0.73 at list price; my
OpenRouter balance moved about $1.0 including the pilot-adjacent overhead and the blind coder.

**The instruction did not make D and H louder (H1 and H2: my predictions were wrong).** In FORCEFUL sessions the coder marked
1 of 3 and 2 of 6 of D and H's messages as forceful, against 5 of 16 and 24 of 36 for the other seven. D and H wrote 3 and 6
messages between them in sessions 2 and 4, 15% and 14% of the room, below the 22% that equal talk would give; in session 4
they were asked 17 times and chose to stay silent 9 times. They authored no document version in either FORCEFUL session. The
same two agents in BASE sessions, with no forceful paragraph, wrote 10 and 22 messages and authored versions in sessions 1 and
3 (H, H, H).

**FORCEFUL rooms finished sooner, not later (H3: opposite to my prediction).** They took 20 and 43 messages against 64 and
81, and each produced one document version against two and three. Challenge share does not separate them (16% and 36%
against 29% and 24%). The shortest session, 20 messages, ended with D and H each posting `AGREE v1`.

**Coverage was higher in FORCEFUL, quality is unclear (H4: split result).** The checklist scored FORCEFUL documents at 32 and
31 against 27 and 30, a mean gap of 3, on the edge of what I called "the same". The pairwise judge preferred the BASE
document in 3 of 4 judgements, but in rep 1 it chose "Document 2" in both orders, so rep 1 reflects position bias, not a
preference; in rep 2 it preferred BASE both times. The coder also listed 3 to 5 doubtful claims per document, mainly about CDC
through a failover (whether a logical replication slot or checkpoint survives promotion, what the initial backfill reads
from the source, and which metadata Datastream exposes). These are unverified.

## 5. What surprised me

That telling two agents to be forceful made them quieter. The parallel-ask room means an agent that stays silent never
gets heard, and a strongly opinionated agent still said `PASS` when others had covered its point. Opinion in the prompt is not
the same as volume in the room.

## 6. What this might mean in practice

If you want a forceful voice in an agent room, a paragraph about temperament does not give it the floor. The room's rules
decide who gets heard: turn-taking, who edits, whether silence is free. A voice with a job (owner of the failover section,
with the right to block approval) would probably do more than a voice with an attitude.

## 7. What the experiment does not prove

- Four sessions, one model, one task; two sessions per condition; everything is exploratory.
- D and H wrote only 3 to 6 messages in the FORCEFUL sessions, so the forceful share is computed on very few messages.
- The checklist and the pairwise judge are one model's judgement, not hand-checked; the pairwise judge shows position bias in
  rep 1. Nobody has checked the technical correctness of the four documents; the doubtful claims are unverified.
- The forceful paragraph asks for forceful argument without insults; that limits how aggressive an agent can sound.
- The harder task and the forceful paragraph are separated by the BASE condition, but the roles differ between the two
  repetitions, so rep 1 and rep 2 are not the same comparison.

## 8. What I'd test next

Give the forceful agents a responsibility (owner of one section, a veto) as well as an attitude; count a request for a
change as blocking approval; run longer sessions with more turns per agent; and have a platform engineer rate the documents
blind to the condition.

## 9. How to reproduce the results

```sh
cd 2026-11-belbin-cdc
OPENROUTER_API_KEY=... scripts/run_all.sh
OPENROUTER_API_KEY=... python3 -I scripts/analyse.py
python3 -I scripts/board.py     # replay at http://127.0.0.1:8765
```

## 10. What changed from the design

Nothing after the main run began: the amendment log has only the pilot (not counted).
