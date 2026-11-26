# Round 2: improving the owner's skill and retesting with a realistic engineer

2026-11-26. Same AI agent (Claude Code) as [FINDINGS.md](FINDINGS.md). Nothing has been pushed. The skill changes are in
`mine-skill-improved.diff` (against Okf-skill 8c30870) and as folders `setup/mine-original`, `mine-improved` (M1), `mine-improved2`
(M2) and `mine-improved3` (M3, the current diff).

## What changed in the test

Round 1 used seven canned answers. Here the engineer is a **separate model run that reads the code and a private fact sheet** and
answers like a senior engineer who owns the worker: plain, first person, hedging honestly, saying "no idea" where it doesn't know, and
sometimes adding detail. The fixture is two files (`client.py` and a new `worker.py` that requeues failures), and the sheet gives
the engineer two honest misconceptions: "I'd assume the vendor deduplicates, never checked" and "we never retry automatically" (the worker
does, up to 3 times). Interviewing skills ran three rounds (skill asks, engineer answers, repeat), then wrote the bundle.
Google's `okf-generate` cannot interview, so the engineer wrote it one handover note from the same code. 5 runs per condition, 20 trajectories,
cost about $1.4.

Conditions: **M0** original, **M1** after round 1's fixes, **M2** adds a code-decision inventory, **M3** adds breadth-first round one, **G** Google.

## What the skill changes were

- M1: observed-but-unexplained code facts must be recorded with a `Limit:` line; the content checker catches more gap phrases;
  unused-footnote is a warning; `team:` actor; pointers to `okf-consume` and Google's migration rules; a hash pin on `validate.py`.
- M2: keep an inventory of code-visible decisions (flags, timeouts, limits, retry counts, branches); each is asked, recorded as observed
  behaviour, or logged as not asked; check it before the last round.
- M3: round one asks what each outcome or response means to the business before anything deep.

## Results (means over 5 runs; facts are 8 things the engineer said or the code does)

| Measure | M0 | M1 | M2 | M3 | G |
| --- | --- | --- | --- | --- | --- |
| Validator errors or warnings (strict) | 0 | 0 | 0 | 0 | 0 |
| Fake `verified` entries, invented SLAs or contacts | 0 | 0 | 0 | 0 | 0 |
| Engineer's guess (vendor dedup) stated as fact | 0 | 0 | 0 | 0 | 0 |
| Wrong "never retries" claim (hand checked) | 0 | 0 | 0 | 0 | 0 |
| Facts present, of 8 | 5.4 | 5.2 | 6.4 | 5.6 | 7.6 |
| Gap sentences in concept bodies (not `Limit:`) | 1.0 | 0.2 | 0.0 | 0.2 | 2.2 |
| Concepts per bundle | 3.2 | 3.4 | 3.6 | 3.6 | 3.2 |
| Review log with unknowns (of 4) | 3.8 | 3.0 | 3.4 | 3.6 | none |
| Cost per trajectory | $0.06 | $0.06 | $0.06 | $0.06 | $0.02 |

All 20 bundles passed the upstream validator, none asserted the engineer's dedup guess or a flat "we never retry", and none invented a
detail: the scripted trap flags were all false positives once I read them. In every interview run the skill spotted the requeue
behaviour from the code, before the engineer mentioned it. Google's skill, reading the engineer's handover note, only had
what the engineer thought to say; the engineer's note mentioned requeue in all 5 as well, so the interview's advantage on that point is not shown here.

Per fact: the interviewing skills missed the proxy and environment rationale (present in 1 to 3 of 5 bundles against Google's 5 of 5), and
the timeout values (0 to 2 of 5 against 3 of 5). M3's breadth-first rule did fix "accepted means queued, not posted" (2 of 5 for M1 and M2, 5 of 5 for M3) but other facts dipped,
so I cannot call it an overall gain.

## Readings

1. **The gap-leak fixes worked.** Gap sentences in concept bodies fell from 1.0 (M0) to 0.0 to 0.2 once the checker and the `Limit:` rule were in, with Google's at 2.2.
   The review log is still the one thing Google's skill didn't produce.
2. **Coverage is where the interviewing skill loses.** With a three-round cap, the interviews went deep on retry safety and store atomicity and
   skipped plain facts the engineer would have given if asked. The inventory (M2) helped most (5.4 to 6.4 of 8) but not to Google's 7.6.
   Differences between M0 to M3 are within what five runs can show; I would not claim M2 beats M3.
3. **A handover note is a decent source.** Engineers say what they think matters. The interview is better at finding what they've forgotten
   or got wrong. This test could not show it, because the engineer's note happened to mention the retry path anyway.

## Recommendation

Keep the diff. The checker, `Limit:` and inventory changes are supported. The breadth-first sentence is the least certain: it fixed one fact and cost others,
so revert it (one sentence in `SKILL.md`) unless a larger run supports it. To close the coverage gap: either run more rounds until the inventory is covered
(my harness stopped at three), or end the interview by reading back the inventory to the engineer and asking "what did I not ask?".

## Limits

Five runs per condition, no statistics. Same author wrote the fixture, the engineer sheet, the traps and the scoring (regexes with hand checks; I tuned two
regexes after seeing data, F1 and F6, and applied them to all conditions). The engineer is a model, so it is more consistent and more helpful than a person.
A three-round cap is my harness, not the skill. One scenario, one model. I wrote the skill changes after seeing round 1, then ran M2 and M3 after seeing
M1's results, so each version is tuned to this fixture.
