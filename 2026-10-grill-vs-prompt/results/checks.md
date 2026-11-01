# Checks on the runs

- **Runs:** 140 measured runs: 35 ticket-only (scripted) and 105 interviews (G, S, K, 35 each). All were graded; none
  was rerun or dropped. Every run passed its ticket's own tests and the existing 25 tests.
- **Model and effort:** every turn context in every Codex session file (354, subagents included) records
  `gpt-5.6-luna` at effort `medium`.
- **Isolation:** no agent's event stream mentions the hidden tests, the briefs, the references or the experiment
  folder. (A text search for "hidden/" matched three agent messages saying "hidden/missing accounts" and
  "hidden/404"; none is a path.)
- **Grading:** hidden JUnit tests after each session, protected files restored from the app first (`scripts/grade.py`).
- **Developer audit:** `scripts/audit.py` (judge `openai/gpt-6-luna`) read every developer reply against its brief and
  the agent's message. It found no leak in 103 of 105 interviews. It flagged two, both K runs on L2 (i080, i093): the
  agent asked what should happen if the case or the new assignee "does not exist", and the reply gave L2 rc (the new
  assignee must be assigned to the case's account; otherwise 400). The question was about invalid assignees, which is
  rc's subject, but it asked about IDs that don't exist, not who is eligible, so the judge's reading is fair. Both runs
  met rc. **Sensitivity:** counting those two as not met, K's few-flat score is 17 of 25 instead of 19, and K's total
  23 of 75 instead of 25. No hypothesis changes: hypotheses 1 and 2 don't involve K, and hypothesis 3 uses M1, N1 and
  N2 only.
- **Reply rules:** the judgement calls applied in every arm are in the README's amendment log (2026-11-01).
- **Stalls:** 8 interview turns were ended by the watchdog (G 7, S 1); in each the questions had been posted and were
  answered as usual. No turn needed "Carry on."
- **Blinding:** runs had anonymous IDs in shuffled order, but G's format (❓ **Qn**) was recognisable, and S and K were
  often distinguishable by length. The audit is the check on the replies.
