# Which kind of team finds the mistakes in a design? Nine agents review a draft with ten planted flaws. Report (experiment PLF)

**This experiment was designed and run with an AI agent** (Claude, working for me): it wrote the design, the draft and its ten
flaws, the room, the analysis and this report. I asked for the experiment (a planted-error review comparing Belbin roles,
all-sceptic, all-agreeable and no-role teams) and paid for it from my OpenRouter credit. I have not independently checked that
each planted flaw is wrong in the way `flaws.json` says, nor reviewed the agreed documents.

2026-11-20. Design: [README.md](README.md), frozen after four pilots (its amendment log records every change) and before the main
run. Event log: [results/events.sqlite](results/events.sqlite). Numbers: [results/analysis.json](results/analysis.json). The 20 final
documents: [results/docs/](results/docs/). Flaws and how each counts as fixed: [flaws.json](flaws.json).

## 1. What I wanted to find out

A draft design (a highly available GKE platform with Cloud SQL and change data capture into BigQuery) contains ten known flaws.
Nine agents must agree a version the team can build from. Which team leaves the fewest flaws in what they agree: nine with Belbin
roles, nine sceptics, nine agreeable agents, or nine with no personality? And is the gap in finding the flaws or in fixing them?

## 2. What I predicted

H1 sceptic teams leave at least 2 fewer flaws than no-role teams; H2 agreeable teams leave at least 1 more; H3 Belbin teams do
not differ from no-role teams by 1 or more; H4 sceptic teams raise at least 1 more false alarm per session; H5 the found-but-not-
fixed gap is largest in agreeable teams.

## 3. How I tested it

Nine `gpt-5.6-luna` agents per session (OpenRouter, low reasoning effort), the same room rules, one shared document that starts
as the draft, compare-and-swap edits, no speaking order; a session ends when all nine approve the same version, when the room
goes quiet, or at 120 messages. One paragraph differs by condition (none; a Belbin role each; all nine sceptical by temperament;
all nine agreeable by temperament). **Agent I is the draft's author in every condition** and defends it. The task asks the team to
agree a design so the build can start: confirm version 1 or amend it. Five sessions per condition, 20 in all, four at a time.

Two blind coders (`openai/gpt-6-luna` primary, `anthropic/claude-haiku-5.5` second) read each transcript with speakers
anonymised, the draft, the final document and `flaws.json`. They agree on 99.5% of "found" judgements and 94.5% of "fixed"
judgements (200 flaw-by-session judgements). The headline numbers below are the primary coder's; the second coder's have the same
pattern. Exploratory: five sessions per condition.

## 4. What happened

Flaws out of 10, primary coder, one number per session:

| Team | Left in the agreed document (lower is better) | Mean | Found in discussion | Found but not fixed | False alarms | Messages |
| --- | --- | --- | --- | --- | --- | --- |
| No personality | 1, 1, 0, 2, 1 | 1.0 | 9.4 | 0.6 | 0.4 | 46 to 89 |
| Belbin roles | 1, 1, 0, 1, 1 | 0.8 | 8.4 | 0.2 | 0.6 | 37 to 83 |
| All sceptics | 0, **10**, **10**, 0, 0 | 4.0 | 9.2 | 3.8 | 0.6 | 25 to 88 |
| All agreeable | 2, 3, 3, 1, 2 | 2.2 | 8.4 | 1.2 | 0.2 | 29 to 57 |

**Finding the flaws did not depend on personality.** Every team found between 8 and 10 of the 10 in almost every session (means 8.4
to 9.4). The first messages of nearly every session list most of them. The difference is what happened next.

**Agreeable teams left more flaws in what they approved (H2: supported).** 2.2 against 1.0 for no personality, a difference of
1.2 (bootstrap 95% interval 0.4 to 2.0; the second coder gives 2.4 against 1.6). They wrote the fewest messages (29 to 57),
made one accepted edit each, had no edit conflicts, and approved. They found as many flaws as the no-role teams (8.4 against 9.4)
but fixed fewer.

**Sceptic teams were either the best or the worst (H1: not supported).** In the three sessions where they agreed, they left **0**
flaws every time, the best result of any team. In the other two (sessions 7 and 11) they found 9 and 10 flaws, all nine refused to
approve version 1, they said what the replacement must contain, and **nobody wrote the replacement**. The room went quiet at 25
and 32 messages with the unamended draft, ten flaws remaining. In session 11 Agent I wrote "I will replace it with a revision"
and did not. By the convention I fixed in advance (the agreed version, or the last version if there is none), these count as
ten flaws left, which gives the sceptics a mean of 4.0, three higher than no personality, with an interval (-1.2 to 7.2) that
includes zero.

**Belbin roles made no difference (H3: supported).** 0.8 against 1.0, a difference of -0.2 (interval -0.8 to 0.4). The roles
showed no benefit over no personality here.

**False alarms were rare (H4: not supported).** 0 to 2 a session in every team (means 0.2 to 0.6; the second coder 0.2 to 1.6, highest in
the agreeable teams). The sceptics were not more likely to attack correct text.

**The gap was not where I predicted (H5: not supported).** The found-but-not-fixed count was largest in the sceptic teams (3.8) because
of the two stalled sessions; it was 0 in the three that agreed. For the agreeable teams it was 1.2, against 0.6 for no personality.

**Nobody rubber-stamped.** In none of the 20 sessions did the team approve version 1 as it stood. Every team posted at least one
revision or refused to approve.

**Cost.** $2.78 at list price for the 20 sessions; my OpenRouter balance moved $3.13, and about $0.12 more for the two coders.

## 5. What surprised me

That the sceptics' failure was a coordination failure, not a thinking one. Nine agents agreed the draft was wrong and agreed on
every correction and still produced no document, because writing the revision was nobody's job. A room of sceptics is good at
saying no and has no one assigned to say what instead.

## 6. What this might mean in practice

If you put agents in a review loop, give someone the job of writing the revision. Temperament changes what the team does after it
spots a problem more than whether it spots it: sceptics refused to move without a revision, agreeable agents moved on with
fewer fixes, and agents with no personality sat in the middle and finished. A "block until fixed" rule with no designated author
can deadlock.

## 7. What the experiment does not prove

- One model, one draft, ten flaws, five sessions per condition. Everything is exploratory; the sceptic result rests on two stalled
  sessions out of five.
- I wrote the flaws and checked each against my own knowledge of Google Cloud, with no independent review. The coders judge "found"
  and "fixed" against the criteria in `flaws.json`; they agree closely with each other but could share a misreading. A 12-session
  sample of the primary coder's flaw-by-flaw judgements is in `results/coded_sample_for_hand_check.csv` for you to check.
- The design needed three changes after pilots (a harder draft, a defending author, a sign-off framing) because nine strong
  reviewers asked to review caught every flaw whatever their temperament; the result applies to the sign-off framing, not to an explicit
  review. Those changes are in the amendment log.
- The coders also counted 3 to 6 real defects per session that I had not planted ("other valid issues"); they are not scored.
- The temperament paragraphs are two sentences, and Agent I defends the draft in every team, which may inflate the sceptics' stalls.
- Compare-and-swap editing changes the dynamics; no memory between sessions.

## 8. What I'd test next

Give one agent in each team the job of writing the revision (an editor), and see whether sceptic teams then lead the table; make
approval need a closed list of objections rather than silence; vary how many flaws the draft has and how hard they are; and have a
platform engineer rate the final documents blind to the condition.

## 9. How to reproduce the results

```sh
cd 2026-11-planted-flaws
OPENROUTER_API_KEY=... scripts/run_all.sh          # 20 sessions, four at a time, then merges
OPENROUTER_API_KEY=... python3 -I scripts/analyse.py
python3 -I scripts/board.py                        # replay at http://127.0.0.1:8765
```

## 10. What changed from the design

See the amendment log in the README: four pilots (the pilot rule fired three times), a defending author and two more flaws, a task
reframed as a sign-off, a fix to the second coder, and the main run's results.
