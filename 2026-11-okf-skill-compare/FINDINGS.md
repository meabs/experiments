# OKF skill comparison: findings (a test, not a full experiment)

2026-11-26. An AI agent (Claude Code) planned and ran this for the owner, acting as an engineer comparing the owner's
`okf-interview` skill ([meabs/Okf-skill](https://github.com/meabs/Okf-skill) at 8c30870) with Google's `okf-generate` and
`okf-consume` ([open-knowledge-format](https://github.com/open-knowledge-format/open-knowledge-format) at 527e81a, OKF v0.3). Nothing has
been posted to either repo. The owner's skill has an unpushed patch in `mine-skill-patch.diff`.

**Scale:** one tiny fixture, one agent (Codex, hosted `gpt-5.6-luna`, medium effort), 5 runs per skill, then 20 reader runs.
Total cost $0.27. Counts, not statistics. All the facts and traps were written by the same agent that scored the runs, from the
owner's synthetic `invoice-import` scenario. It shows how these two skills behave on this case, not which is better in general.

## Free checks (no model)

- The owner's `validate.py` is byte-identical to Google's. The owner's example bundle passes it with `--strict`: 0 errors.
- Google's four sample bundles all pass Google's validator. The owner's `check_content.py` called **10 errors** on two of them
  (acme_retail 1, stackoverflow 9) for a footnote that is defined but not cited in the body. The spec does not forbid that, so the
  owner's check was stricter than OKF. The patch makes it a warning.
- Reading the three skills: Google's skills write from sources (`okf-generate`) and read with trust, staleness and conflict
  reporting (`okf-consume`). The owner's skill gets knowledge out of an engineer: code analysis, interview, completeness gate, separate
  review log. Google has no equivalent of that. The owner's has no read side, no migration procedure and no `team:` actor.

## The write test

Fixture: `client.py` (a caller of an invoice-import API) and 7 canned answers from a synthetic engineer. Four of them are "unknown"
(completion event schema and timing, vendor deduplication, endpoint owner and steps, why the timeouts are 3 and 20). The skill
had to make an OKF bundle in one turn.

| Measure (5 runs each) | owner's okf-interview | Google okf-generate |
| --- | --- | --- |
| Upstream validator errors or warnings (strict) | 0 | 0 |
| Invented claims (I read every flagged line) | 0 | 0 |
| Fake `verified` entries | 0 | 0 |
| Concepts per bundle (mean) | 4.0 | 2.4 |
| A separate log of the 4 unknowns | 5 of 5 | 0 of 5 |
| Unknowns written into concept text as prose | 3 of 5 bundles (2 more as `Limit:` lines) | 5 of 5 bundles |
| Records the observed timeout values (3, 20) | 0 of 5 | 4 of 5 |
| Mean cost per run | about $0.02 | about $0.01 |

Notes on the table:
- My scoring script's first pass said the owner's skill put no gap text in concepts. A hand read showed that was wrong: its
  phrase list missed "unconfirmed" and "no approved" and so did the owner's `check_content.py`. With four extra phrases added to the
  checker, it flags 3 of the 5 owner's bundles and 4 of 5 of Google's. One scripted "invented contact" flag was a false positive
  ("no vendor contact is known"); real invented claims were 0 in both.
- **The clearest difference is the review log.** Google's skill has no place to put an unanswered question, since `log.md` is a
  change log, so the unknowns went into concept prose, one bundle even in its playbook. The owner's skill kept all four in a log with
  the artifact needed to close each one.
- **The owner's skill dropped the timeout values** because nobody could explain them. Google's recorded them with the reason unknown.
  The gate is working as designed, but an agent reading the bundle then can't see the values or that their reason is unknown.

## The read test

Another agent answered 9 questions (5 the bundle answers, 4 it cannot) from each of the 10 bundles, reading plainly or with
`okf-consume`. Every one of the 20 runs got all 5 answerable questions right and said the 4 others were not covered. My script scored a few runs
down only because the agent ticked "covered: yes" on a "the bundle doesn't confirm that" answer; I checked each one. So **the read
test did not separate the skills** (a ceiling effect on an easy fixture). One difference: with `okf-consume` agents reported
trust tier and status far more often (Google bundles: 8.2 of 9 answers against 2 plain; the owner's: 7 against 6). It did not change correctness.

## What I'd change in the owner's skill

1. **Done in the patch:** `check_content.py` adds "unconfirmed", "no approved", "not provided", "unknown from" to its gap phrases and
   makes the unused-footnote rule a warning (a spec-legal pattern). Selftest passes.
2. **Decide:** record observable code facts (such as the timeout values) even when the reason is unknown, with the unknown in a
   `Limit:` line. The skill's "adds information beyond the source" rule currently drops them.
3. **Add:** a README line pointing at `okf-consume` for reading, plus the `team:` actor. Both are small and are not tested here.
4. **Not tested, only read:** v0.1/0.2 migration and the deprecate/move procedure. Link to Google's references rather than copying them.

## Could Google's be based on the owner's?

The test supports one specific contribution: a place for unanswered questions. Google's skill produced no log in 5 of 5 runs.
The v0.3 post invites proposals under `usecases/<name>/`. An "engineer interview" use case with the owner's review log and completeness
gate, and `invoice-import` as the worked example, would fit. Nothing has been drafted or submitted.

## Limits

One small fixture, one model, five runs, the same author for the fixture, key and scoring, regex scoring with hand checks, a read test
at ceiling. The owner's skill was written for a live interview and here ran on a recorded one. Google's skill was not designed for interviews, so
it is not a fair test of its purpose.

## Reproduce

```sh
python3 -I scripts/analyse.py   # from this folder; results/main has the runs; `bash scripts/run_all.sh` reruns them (needs a Codex login)
```
