# Does giving a team of AI agents Belbin team-role personalities change the design they write? Report (experiment BLB)

**This experiment was designed and run with an AI agent** (Claude, working for me): it wrote the design, the room, the
analysis and this report. I asked for the experiment, chose the Belbin roles as the persona set and the GKE design task,
and the OpenRouter credit paid for it. I have not yet reviewed the design documents for technical correctness.

2026-11-20. Design: [README.md](README.md), with every later change in its amendment log. Event log:
[results/events.sqlite](results/events.sqlite). Numbers: [results/analysis.json](results/analysis.json). The four agreed
documents: [results/docs/](results/docs/). Replay the sessions: `python3 -I scripts/board.py`.

## 1. What I wanted to find out

Nine agents write one design document together for a highly available GKE cluster platform. In one condition each agent
gets one of the nine Belbin team roles as its personality, in its system prompt. In the other, all nine are identical.
Do the roles show, change how the team works, and change the document?

## 2. What I predicted

H1 Belbin agents are recognisable (a blind coder names the assigned role for at least a third, against 1 in 9 chance;
control no better than chance). H2 Belbin rooms do not write a more complete design (checklist totals within 3 of 24).
H3 Belbin rooms challenge more and take more messages to agree.

## 3. How I tested it

`gpt-5.6-luna` for all nine agents (OpenRouter, low reasoning effort), the same shared-room instructions, a Belbin
paragraph per agent in one condition (role, short description, strengths, allowable weaknesses, from Belbin's page) and
none in the other. Two sessions per condition, interleaved; in the second repetition the roles are assigned to letters in
reverse order. One shared document with compare-and-swap edits, no speaking order, agreement of all nine ends a session.
Exploratory: four sessions.

## 4. What happened

| Session | Condition | Messages | Document versions (authors) | Rejected edits | Challenge share | Checklist (of 24) | Words |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Belbin | 41 | 1 (D) | 4 | 10% | 23 | 1,211 |
| 2 | Control | 34 | 1 (C) | 6 | 0% | 23 | 1,387 |
| 3 | Belbin, roles reversed | 45 | 2 (I, I) | 11 | 23% | 23 | 1,349 |
| 4 | Control | 35 | 1 (H) | 6 | 6% | 23 | 1,113 |

All four sessions ended with all nine agents agreeing, and no session hit the cap. Cost $0.42 at list price for the
sessions; the OpenRouter balance moved $0.55 including the blind coder.

**The roles did not show (H1: my prediction was wrong).** The coder named the assigned role for 2 of 14 Belbin agents
(14%, against 11% by chance). It mostly called them Completer Finisher (7) or Specialist (4), which is what almost every
agent in these rooms sounds like: careful, technical and checking details. The control agents, which have no role, were
labelled Specialist 6 of 9 times. A Plant, a Shaper and a Resource Investigator did not read as different from a Specialist
in this task.

**The team worked a little differently (H3: directionally, on two sessions each).** Belbin rooms used 41 and 45 messages
against 34 and 35, and challenged more (10% and 23% of messages against 0% and 6%). Session 3 was the only session to
produce a second version of the document. Rejected edits were also higher in the Belbin rooms (4 and 11 against 6 and 6),
though one of them is in the range of the controls. With two sessions per cell, this is a lead, not a result.

**The documents were the same by this measure (H2: supported, but the checklist cannot tell).** Every session scored 23 of
24; each lost the same point on upgrades and maintenance. A measure with no spread cannot show a gain, so this does not
show that the roles make no difference to design quality, only that coverage and specificity are at the ceiling for this
model on this task.

**Agreement was cheap.** Nine agents approved version 1 in three of four sessions. In session 1 several agents asked for
changes after version 1 (for example, evidence that the two surviving zones can carry peak load) and the others kept
approving, but nobody posted a revision. Nine agents also tried to draft at the start: eight edits were rejected by
compare-and-swap in the pilot, between 4 and 11 in the sessions.

**Claims for a person to check.** The coder listed three or four doubtful statements per document, for example "Cloud NAT per
zone" (Cloud NAT is regional), "regional GKE NEGs" (container-native load balancing uses zonal NEGs), and automatic
rollback on an SLO breach being presented as built in. These are not scored and are the coder's, not mine; a platform
engineer should read the four documents before anyone builds from them. All four are in `results/docs/`.

## 5. What surprised me

How little the persona text changed the voice of the room. Nine very different job descriptions produced messages that a
reader would put in about the same two bins. The task pulls the agents towards one register (precise, technical, hedged),
and the role paragraph does not override it.

## 6. What this might mean in practice

If you want a team of agents to behave like a team with different perspectives, a paragraph of personality in the prompt
does not appear to be enough on a task with a clear technical right answer. The differences I saw (more challenge, a second
version) were small. A role that comes with a different job (own the failure analysis, own the rollout plan) would probably
do more than a temperament.

## 7. What the experiment does not prove

- Four sessions, one model, one task. Everything is exploratory.
- The checklist is at the ceiling (23 of 24 everywhere) and measures coverage and specificity, not correctness. A person
  has not reviewed the documents; the coder's doubtful claims are unverified.
- The coder is another model, not hand-checked (40 messages are in `results/coded_sample_for_hand_check.csv` to check).
  Role recognition used the few substantive messages each agent wrote, 2 to about 6, not the 12 planned (amendment).
- A Belbin paragraph is a thin version of a role that, on Belbin's own page, people can play in more than one way.
- The compare-and-swap rule changes the dynamics: agents learn to wait. The first experiment had no such rule.
- No memory between sessions, so this says nothing about roles that develop over time.

## 8. What I'd test next

Give each agent a role with a different responsibility, not only a temperament; add a rule that agreement counts only after
a revision pass; use a harder, more contested design task where the checklist does not saturate; and have a platform
engineer rate the four documents blind to the condition.

## 9. How to reproduce the results

```sh
cd 2026-11-belbin-gke
OPENROUTER_API_KEY=... scripts/run_all.sh
OPENROUTER_API_KEY=... python3 -I scripts/analyse.py
python3 -I scripts/board.py     # http://127.0.0.1:8765, replay any session
```

## 10. What changed from the design

See the amendment log in the README: the pilot (not counted), the main run, a change to how many messages the role coder
sees (after the run), and one coder retry.
