# Does an editor plus an independent checker leave fewer flaws? The planted-flaw review with a reviser and a checker. Report (experiment PLC)

**This experiment was designed and run with an AI agent** (Claude, working for me): it wrote the design, the room changes, the
analysis and this report. I asked for the follow-up (an independent checker of the revision) and paid for it from my OpenRouter
credit. I have not independently reviewed the flaws or the agreed documents.

2026-11-20. Design: [README.md](README.md), frozen after a smoke test and before the main run. Event log:
[results/events.sqlite](results/events.sqlite). Numbers: [results/analysis.json](results/analysis.json). The 20 final documents:
[results/docs/](results/docs/). Compared with [PLE](../2026-11-planted-flaws-editor/) (editor only) and
[PLF](../2026-11-planted-flaws/) (neither).

## 1. What I wanted to find out

PLE named an editor to write the revision; nobody was assigned to check it, and the neutral team left more flaws than without an
editor. Does adding one agent whose job is to check each revision (Agent C) leave fewer of the ten planted flaws in the approved
document?

## 2. What I predicted

H1 the mean flaws left across all 20 sessions is at most 0.8 (PLE 1.3, PLF 2.0); H2 the neutral team leaves at most 1.2 (PLE 2.0);
H3 at least 19 of 20 sessions reach agreement; H4 the median session is at least 10 messages longer than PLE's; H5 false alarms do
not rise (at most 1 a session on average in every team).

## 3. How I tested it

PLE's set-up (nine `gpt-5.6-luna` agents, the same draft with ten planted flaws, the sign-off task, Agent I the defending author,
Agent E the editor, four team types, five sessions each, two blind coders) plus **Agent C as the checker** in every session. The
comparison sessions (PLE and PLF) were run earlier the same day with the same code, prompts and draft and are not interleaved:
cross-run comparisons. Exploratory.

## 4. What happened

Flaws left in the agreed document, out of 10 (primary coder), per session, with PLE's and PLF's beside them:

| Team | Editor and checker (PLC) | Mean | Editor only (PLE) | Mean | Neither (PLF) | Mean |
| --- | --- | --- | --- | --- | --- | --- |
| No personality | 1, 1, 0, 1, 1 | 0.8 | 3, 2, 2, 2, 1 | 2.0 | 1, 1, 0, 2, 1 | 1.0 |
| Belbin roles | 0, 1, 1, 3, 1 | 1.2 | 1, 2, 0, 1, 1 | 1.0 | 1, 1, 0, 1, 1 | 0.8 |
| All sceptics | 1, 1, 0, 0, 0 | 0.4 | 1, 0, 0, 0, 1 | 0.4 | 0, 10, 10, 0, 0 | 4.0 |
| All agreeable | 2, 2, 1, 1, 1 | 1.4 | 2, 1, 2, 2, 2 | 1.8 | 2, 3, 3, 1, 2 | 2.2 |
| **All teams** | | **0.95** | | **1.3** | | **2.0** |

**The checker reversed the neutral team's rise (H2: supported).** No-personality teams left 0.8 flaws, against 2.0 with an editor
alone (difference -1.2, bootstrap 95% interval -1.8 to -0.6) and 1.0 with neither. The other teams were within noise of PLE: Belbin
+0.2 (-0.8 to 1.2), sceptic 0.0 (-0.6 to 0.6), agreeable -0.4 (-1.0 to 0.2). The mean over all teams, 0.95, is the lowest of the three
runs but misses the 0.8 I set (H1: not supported, narrowly).

**Agreeable teams are still the ones that leave the most.** 1.4 against 0.8 for the neutral team (the second coder: 2.4 against
1.0), as in PLF. A checker did not close that gap.

**Two sessions did not agree (H3: not supported, 18 of 20).** Session 15 (sceptic) and session 18 (Belbin) reached the 120-message cap
with no unanimous approval; their last versions left 0 and 1 flaws. The checker adds rounds: the median session was 86.5
messages against PLE's 64 (H4: supported; my README quoted PLE's median as 68, which was wrong, and the threshold becomes 74, with
the same result). Sceptic teams wrote the most (88, 121, 121, 124, 57), and the checker wrote 13 to 18 messages in four of them.

**The editor and the checker did their jobs.** Agent E wrote 32 of the 51 accepted edits (63%, PLE 58%) and Agent C wrote 5 to 18
messages a session. Sceptic teams had the most rejected edits (6, 6, 12, 5, 2); the figures are in `analysis.json`.

**False alarms rose a little in the Belbin teams (H5: not supported).** Means 0.8 (none), 1.2 (Belbin, one session with 4), 0.2
(sceptic), 0.4 (agreeable); the second coder gives 2.0 for the Belbin teams. Found in discussion was 8.6 to 9.6 of 10 in every team.

**Cost.** $5.41 at list price for the 20 sessions (PLE $4.03, PLF $2.78); my OpenRouter balance moved about $6.7 including the
coders. The two coders agree on 99.5% of "found" and 94.5% of "fixed" judgements. They differ more than before on the sceptic teams
(0.4 against 1.0).

## 5. What surprised me

That the checker mattered most for the team with no personality. The sceptics already questioned everything and the agreeable team did
not question enough, so a named checker changed little for them; the neutral team, which had relaxed once an editor existed, was
brought back. It cost about a third more messages and two sessions that never finished.

## 6. What this might mean in practice

An editor fixes a deadlock; a checker keeps an editor honest. Both together gave the lowest flaws left of the three set-ups, at the
price of long sessions and sometimes no agreement within a cap. The agreeable team's gap persisted through all three set-ups, so a
temperament that avoids confrontation is not repaired by assigning jobs.

## 7. What the experiment does not prove

- One model, one draft, ten flaws I wrote and checked myself, five sessions per cell. The comparisons with PLE and PLF are cross-run
  and not randomised; differences could be run-to-run variation (the neutral team's swings from 1.0 to 2.0 to 0.8 across the three
  runs show how large that variation can be).
- The two coders disagree more here: the second coder gives higher flaws-left for the sceptic and agreeable teams. A 12-session
  sample is in `results/coded_sample_for_hand_check.csv` for you to check by hand.
- Two sessions hit the cap without agreement; a longer cap might have changed their outcome. The "last version" counted for them.
- The checker and editor jobs are short prompts and the agents keep their team temperaments.

## 8. What I'd test next

Run all three set-ups (neither, editor, editor and checker) in the same run, interleaved; vary who the checker is (a sceptic, the
author's critic, a neutral agent); and have a platform engineer rate the final documents blind to the condition.

## 9. How to reproduce the results

```sh
cd 2026-11-planted-flaws-checker
OPENROUTER_API_KEY=... scripts/run_all.sh
OPENROUTER_API_KEY=... python3 -I scripts/analyse.py   # also needs the PLE and PLF analysis.json
python3 -I scripts/board.py
```

## 10. What changed from the design

See the amendment log in the README: the smoke test, the main run's results and a correction to the PLE median quoted in the design.
