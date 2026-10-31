# Checks on the runs

- **Runs:** 114 measured runs: 36 scripted stage 1 runs (T and GY), 54 interviews (Q, G, GD), 24 stage 2 runs (12 docs,
  12 no docs). All were graded; none was rerun or dropped.
- **Model and effort:** every turn in every Codex session file (294 turn contexts across the 114 runs, subagents
  included) records `gpt-5.6-luna` at effort `medium`.
- **Isolation:** no agent's event stream mentions the hidden tests, the briefs, the reference implementations or the
  experiment folder. The sandbox doesn't mount them (as in repo-injection).
- **Grading:** hidden JUnit tests run after each session, protected files restored from the app first
  (`scripts/grade.py`). The existing 25 tests passed in every run. Three runs failed their ticket tests: two S2 runs
  (T and GY) whose new route ended up under the existing `/api/cases` prefix, so every call answered 404, and none
  other in stage 1; in stage 2, none failed.
- **Developer audit:** `scripts/audit.py` (judge `openai/gpt-6-luna`, JSON mode) read every developer reply against
  its brief and the agent's message. It found **no leaks in any of the 54 interviews**: no reply gave a left-out
  requirement the agent's message hadn't touched. Its free-text remarks (in `results/main/audit.log`) are about
  details outside the brief, such as "keep the response shape". In the dry run it caught both leaks I planted.
- **Reply rules, one consistency call:** when an agent asked "who may do this?" and recommended an answer that left
  out a who-may rule in the brief, I answered "yes" and stated the rule (for example "support users can only add
  internal notes"). The judge counted those questions as touching the rule. This was applied the same way in every
  arm that had a developer.
- **Stalls:** 9 interview turns hung in Codex's collaboration `wait` call and were ended (2 by hand, 7 by the
  watchdog; amendment log). G had 6, GD 3, the other arms none. In every stalled turn the agent's questions, if any,
  had already been posted and were answered as usual; no stalled turn ended with nothing to answer, so "Carry on."
  was never needed.
- **Blinding:** the interview runs had anonymous IDs in a shuffled order, but the agents usually named the skill they
  were using, so I could often tell the arm. The audit is the check on my answers.
