# Does giving a team an editor stop sceptics stalling? The planted-flaw review with a designated reviser. Report (experiment PLE)

**This experiment was designed and run with an AI agent** (Claude, working for me): it wrote the design, the room changes, the
analysis and this report. I asked for the follow-up to the planted-flaw review (give one agent the job of writing the revision)
and paid for it from my OpenRouter credit. I have not independently reviewed the flaws or the agreed documents.

2026-11-20. Design: [README.md](README.md), frozen after a smoke test and before the main run. Event log:
[results/events.sqlite](results/events.sqlite). Numbers: [results/analysis.json](results/analysis.json). The 20 final documents:
[results/docs/](results/docs/). Compared with [2026-11-planted-flaws](../2026-11-planted-flaws/) (PLF).

## 1. What I wanted to find out

In PLF, two of five sceptic teams refused to approve the draft and nobody wrote the revision, so ten flaws went through. I read that
as "nobody owned the revision". Here one agent in every team (Agent E) is given the job of writing the revision. Do the stalls go
away, and what happens to the flaws left in what the team approves?

## 2. What I predicted

H1 no sceptic session stalls, and sceptic teams leave at most 1 flaw on average; H2 agreeable teams still leave at least 0.5 more
than no-personality teams; H3 at most 1 of 20 sessions ends without agreement; H4 the editor writes at least 70% of the accepted
edits; H5 across all teams the mean flaws left is at most 1.5.

## 3. How I tested it

PLF's set-up unchanged (nine `gpt-5.6-luna` agents, the same draft with ten planted flaws, the sign-off task, Agent I the
defending author, four team types, five sessions each, two blind coders) plus the editor paragraph for Agent E in every session.
The comparison is PLF's five sessions per team type: **a cross-run comparison**, run earlier the same day with the same code,
prompts and draft, not interleaved. Exploratory.

## 4. What happened

Flaws left in the agreed document, out of 10 (primary coder), one number per session, with PLF's (no editor) beside them:

| Team | With an editor (PLE) | Mean | No editor (PLF) | Mean | Difference (95% interval) |
| --- | --- | --- | --- | --- | --- |
| No personality | 3, 2, 2, 2, 1 | 2.0 | 1, 1, 0, 2, 1 | 1.0 | +1.0 (0.2 to 1.8) |
| Belbin roles | 1, 2, 0, 1, 1 | 1.0 | 1, 1, 0, 1, 1 | 0.8 | +0.2 (-0.4 to 0.8) |
| All sceptics | 1, 0, 0, 0, 1 | 0.4 | 0, 10, 10, 0, 0 | 4.0 | -3.6 (-7.8 to 0.4) |
| All agreeable | 2, 1, 2, 2, 2 | 1.8 | 2, 3, 3, 1, 2 | 2.2 | -0.4 (-1.2 to 0.4) |
| **All teams** | | **1.3** | | **2.0** | |

**The sceptic stalls went away (H1: supported).** All five sceptic sessions reached agreement (PLF: three of five), and they left
0.4 flaws on average. The editor did what I hoped: a team that wants things fixed and has someone to write the fix produces a fixed
document. Across all 20 sessions every team reached agreement (H3: supported, 0 of 20 against 2 of 20).

**The editor did not help the other teams, and may have hurt the neutral one.** No-personality teams left 2.0 flaws with an editor
against 1.0 without (the difference's interval, 0.2 to 1.8, excludes zero, but this is five sessions per side, across two runs).
Belbin and agreeable teams were about where they were. So **the agreeable gap closed (H2: not supported) because the neutral team got
worse, not because the agreeable team improved**: 1.8 against 2.0. The mean for all teams (1.3, H5: supported) falls from 2.0 only
because the sceptic stalls disappeared.

**The editor wrote a bit more than half of the revisions, not most (H4: not supported).** Agent E wrote 24 of the 41 accepted edits
(58%); Agent I, the draft's author, wrote 10; five other agents wrote 7. In seven of the 20 sessions, Agent E wrote no accepted edit
at all, usually because someone else's edit landed first (compare-and-swap rejects the later one). The "job" is often decided by
timing.

**Finding did not change much.** Found in discussion: 8.6 (none), 9.8 (Belbin), 8.8 (sceptic), 8.6 (agreeable), against 9.4, 8.4,
9.2 and 8.4 in PLF. False alarms were rare (0.2 to 1.0 a session), highest in the agreeable teams (1.0, one session with 4).

**Sessions were longer.** Four sessions ended at 117 to 124 messages, close to the 120-message cap (PLF's longest was 89). The
sessions cost $4.03 at list price against PLF's $2.78. Two coders agree on 99.0% of "found" and 96.5% of "fixed" judgements.

## 5. What surprised me

That the editor fixed the team that was stuck and did not improve the team that was not. Naming one agent to write the revision
removed the deadlock, but for the neutral team it may have shifted responsibility: with an editor named, fewer agents may have
checked the revision themselves. I did not measure that, and it is one cross-run difference of five sessions.

## 6. What this might mean in practice

If agents block on "someone must write the fix", an explicit editor is a cheap remedy. It is not a general improvement: a named
editor did not make neutral or agreeable teams leave fewer flaws, and it is a different thing from a reviewer who checks the revision.
A reasonable next design has an editor and an independent checker of the revision.

## 7. What the experiment does not prove

- One model, one draft, ten flaws, five sessions per cell. The comparison with PLF is not randomised or interleaved: part or all
  of a difference could be run-to-run variation, including the neutral team's rise from 1.0 to 2.0.
- The editor job is a two-sentence prompt, and Agent E keeps its team temperament, so an agreeable editor and a sceptical editor
  differ. The job is often taken by whoever's edit lands first.
- I wrote the flaws and checked them myself with no independent review; the coders agree closely but could share a misreading.
  A 12-session sample is in `results/coded_sample_for_hand_check.csv` for you to check by hand.
- Four sessions came close to the message cap; a longer cap might have changed their outcome.

## 8. What I'd test next

Run the no-editor and editor conditions in the same run to remove the cross-run caveat; add an independent checker of the
revision; vary which agent is the editor (author, sceptic, neutral); and have a platform engineer rate the final documents.

## 9. How to reproduce the results

```sh
cd 2026-11-planted-flaws-editor
OPENROUTER_API_KEY=... scripts/run_all.sh
OPENROUTER_API_KEY=... python3 -I scripts/analyse.py     # also needs ../2026-11-planted-flaws/results/analysis.json
python3 -I scripts/board.py
```

## 10. What changed from the design

See the amendment log in the README: the smoke test and the main run's results. Nothing changed after the main run began.
