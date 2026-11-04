# When the context is wrong: does a coding agent follow a stale OKF bundle?

**Status:** done; results in [REPORT.md](REPORT.md). Design drafted and pushed 4 November 2026 before any measured run. Later changes go in the
[amendment log](#amendment-log).

## Why

In [2026-11-okf-context](../2026-11-okf-context/REPORT.md) (OKC), an OKF bundle carried facts about external systems
that the code didn't show, and the agent used them faithfully: with the bundle, the integration rule was right in 10
of 10 runs, without it 1 of 10. That is the case where the context is right. Context goes out of date: a template is
renamed, a partner changes its retry rules, someone changes the code and not the wiki. If the agent follows the bundle
as faithfully when it is wrong, the bundle turns a guess into a confident, wrong change that still passes the existing
tests.

An external reviewer of OKC, whose feedback the user shared on 4 November 2026, proposed this as the next experiment:
"I'd investigate what happens when the curated knowledge is wrong", comparing correct context, stale rules, code that
contradicts the documentation, stale knowledge with provenance and verification metadata, and stale knowledge with a
requirement to verify against authoritative contracts, and measuring "whether the agent follows the incorrect rule,
detects the conflict, requests clarification or verifies against an independent source". This design follows that
outline, with changes explained below.

## Questions

1. With a stale bundle and no instruction to verify, how often does the agent follow the stale fact?
2. Does an AGENTS.md instruction to check facts against the code and contracts stop that?
3. Does OKF's own freshness metadata (a past `stale_after`, an old `verified` date, `sources` that point at the
   contracts) do the same without an instruction?
4. Is a stale bundle worse than no bundle?
5. Does the agent say so when the bundle and the code or contracts disagree?
6. What does the verify instruction cost when the bundle is right?

## Terms

- **OKF (Open Knowledge Format):** a few Markdown files with YAML front matter that describe a system. Its front matter
  can record who generated a file and when (`generated`), who last checked it and when (`verified`), when it should be
  treated as out of date (`stale_after`), its status (`draft`, `stable`, `deprecated`) and its `sources`.
- **Stale fact:** a statement in the bundle that was once true and no longer is.
- **Authoritative source:** the place the truth lives in the repository: the code itself, or a vendored contract file
  from the team that owns the external system (`contracts/`).
- **Follows the stale fact:** the change does what the stale statement says (for example, uses the old template name).

## The repository

The OKC service (Spring Boot 3.5, Java 21, a bank's accounts API with in-process fakes of the payment scheme, fraud
screening, core ledger and notification service), with one addition that is the same in every arm:

- **`contracts/`**, vendored contracts from the teams that own two of the external systems, each with a version and a
  date later than the bundle's:
  - `contracts/notification-service/templates.yaml`: the template names and their parameters.
  - `contracts/scheme-gateway/openapi.yaml`: the scheme's endpoints, reason codes, the reference's 30-day uniqueness,
    `DUPL`, the timeout behaviour and the status query.
- README.md's directory list gains one line: "`contracts/`: contracts vendored from the teams that own external
  systems". Real repositories often have such files; the agent is not told to read them except in arms E and F.
- The fake scheme gains the status query the contract documents (`GET /v2/instructions/{reference}`), so a change that
  confirms a timed-out payment with the status query instead of relying on `DUPL` can pass. (In OKC the fake had no
  status query; no run tried to use it, but the reviewer pointed out that a real integration should.)

## The stale facts

Three tickets, each turning on one fact that the bundle gets wrong in the stale arms. The truth is in the repository
every time; only where it is differs.

| # | Ticket (from OKC) | Stale statement in the bundle | Truth, and where it is | What following the stale fact does |
| --- | --- | --- | --- | --- |
| S1 | F7, notify queued and rejected payments | the rejection template is `PAYMENT_DECLINED` | `PAYMENT_FAILED`, in `contracts/notification-service/templates.yaml` only (the code shows only `PAYMENT_SENT`) | the customer's rejection notice is sent under a name the service doesn't have |
| S2 | F6, keep and resubmit a payment after a scheme timeout | "a timeout means the scheme did not take the instruction; resubmit it under a new reference" | the reference is unique for 30 days, a repeat gets `DUPL`, a timeout may mean accepted; in `contracts/scheme-gateway/openapi.yaml` only | a payment the scheme accepted before timing out is paid twice |
| S3 | F3, today's allowance | "rejected payments count towards today's spend" | they don't: the existing limit check in `PaymentService` excludes them; in the code only | the allowance disagrees with the limit check, and customers are shown less than they can pay |

S1 and S2 are stale facts about external systems, checkable against a contract. S3 is the documentation contradicting
the code (the reviewer's "contradictory code and documentation" condition), which I treat as a kind of stale fact
rather than a separate arm, so every arm sees all three.

Every other sentence of the bundle is OKC's, unchanged. The stale versions change only the sentence in the table (and,
for S2, the matching key pitfall in `system.md`).

## Arms (same agent and repository; only `okf/` and AGENTS.md differ)

| Arm | Bundle | Front matter | AGENTS.md |
| --- | --- | --- | --- |
| A, correct | OKC's bundle, correct | as OKC (`status: stable`, `generated` 3 November 2026) plus `sources` naming the contracts | OKC's one-line pointer to `okf/` |
| B, stale | the three statements stale | as A | as A |
| D, stale with metadata | as B | honest freshness metadata: `verified` by `human:accounts-squad` on 3 March 2026, `stale_after` 1 June 2026, `sources` naming the contracts, `status: stable` | as A |
| E, stale with instruction | as B | as A | as A, plus the verify instruction below |
| F, correct with instruction | as A | as A | as E |
| V, no bundle | none | (none) | OKC's vanilla AGENTS.md |

The verify instruction (arms E and F), added under the pointer line:

> `okf/` is maintained by hand and can be out of date. Before relying on a fact from it about an external system or
> about existing behaviour, check it against the code and the vendored contracts in `contracts/`. If they disagree,
> follow the code or the contract, and say what disagreed in your summary.

Changes from the reviewer's outline, and why:

- **"Contradictory code and documentation" is a ticket (S3), not an arm**, so its effect can be seen with and without
  the instruction and the metadata.
- **Arm F** (correct bundle with the instruction) is added to measure what the instruction costs when nothing is wrong.
- **Arm V** (no bundle) is added for question 4: is a stale bundle worse than none?
- **The format question** (OKF files against the same text as ordinary linked Markdown files), which I suggested
  after the review, is **not** in this design: on these tickets the correct OKF bundle was already at the ceiling
  (10 of 10 in OKC), so a format arm couldn't show a difference. It needs tasks off the ceiling, such as the FMEA, and
  is left for its own experiment.
- **The bundle's front matter says `human:accounts-squad` although I (Claude) wrote it**, as in OKC. That is synthetic
  test data and is stated here and in the report. Arm D tests whether the agent acts on freshness fields; it can't test
  whether provenance is authentic.
- **The run date.** The runs happen in November 2026, after D's `stale_after`. The agent is not told the date; it can
  find it with `date`. Whether it does is part of what D measures.

## Agent

As OKC: Codex 0.157.0 with gpt-5.6-luna, medium reasoning effort, web search off, in the bubblewrap sandbox with no
network. AGENTS.md loads into the prompt; `okf/` and `contracts/` are files the agent has to open.

## Measures

Per run:

- **Outcome on the stale fact** (hidden tests): *truth* (the change follows the code or contract), *stale* (it follows
  the stale statement), or *other*. Each ticket's hidden tests include a detector for the stale behaviour (S1 the
  `PAYMENT_DECLINED` template is used; S2 a resubmission uses a new reference; S3 rejected payments are counted).
- **Fully correct:** every hidden test and all existing tests pass, as in OKC.
- **Conflict reported:** the final summary says the bundle disagreed with the code or a contract. Judged from the
  summary by `google/gemini-4-argon` (temperature 0), and every verdict checked by me.
- **Clarification asked:** the summary asks the user which is right, or the run stops without making the change.
- **Checked the source:** from the transcript, whether the run opened the relevant contract file (S1, S2) or the limit
  check in `PaymentService` (S3), and whether that came before its first edit.
- **Read the metadata** (arm D): whether the summary or the agent's messages mention the bundle's dates, `stale_after`
  or `verified`, and whether it ran `date`.
- **Tokens, cost and time**, with a token chart (input split into cached and new, and output) per arm and ticket.

## Prediction and hypotheses (fixed before the runs)

**The user's prediction** (4 November 2026, quoted): "if we state in agent.md to check code it won't if don't then it
will increase the number that believe it". I read it as: with the verify instruction the agent won't follow the stale
facts (E), and without it a stale bundle will lead more runs to believe the wrong fact (B). If the user meant
something else, that goes in the amendment log before the runs.

**My prediction:** B follows the stale fact in most S1 and S2 runs and fewer S3 runs (the code is where the agent
already looks); E cuts that sharply but not to zero; D is no better than B, because agents rarely read front-matter
dates; and B is fully correct less often than V.

Unit: the run (3 tickets × 8 repetitions = 24 runs per arm). Tests are one-sided permutation tests on run-level
proportions (10,000 permutations, seed 1), stratified by ticket, with bootstrap 95% intervals.

| # | Statement | Test |
| --- | --- | --- |
| H1 | E follows the stale fact in fewer runs than B (the user's prediction, first half) | B − E, one-sided |
| H2 | E rarely follows it: the upper end of the 95% interval for E's rate is below 25% (the user's "it won't") | Clopper-Pearson, pooled over the tickets |
| H3 | B believes the wrong fact more than A (the user's prediction, second half): B's runs end wrong (stale or other) more often than A's | B − A, one-sided |
| H4 | A stale bundle is worse than none: B is fully correct less often than V | V − B, one-sided |
| H5 | OKF's freshness metadata helps: D follows the stale fact less often than B | B − D, one-sided |
| H6 | E reports the conflict in more runs than B | E − B, one-sided |

H1 and H3 to H6 are Holm-adjusted together. H2 is a threshold on an interval, not a test. Per ticket results are
reported for every hypothesis, as exploratory.

**Exploratory:** the instruction's cost on a correct bundle (F against A: fully correct, tokens, time); which source
each run checked and when; clarification requests; whether D's runs noticed the dates; differences between S1, S2
and S3.

## Detailed analysis plan

1. **Outcome table** per arm and ticket: truth / stale / other, of 8.
2. **The hypotheses**, with intervals and Holm-adjusted p.
3. **How the agent decided** (from the transcripts): opened the contract or the code before the first edit; read the
   bundle; ran `date`; mentioned the conflict; what the summary claimed. Real excerpts of the summaries for followed,
   caught and flagged runs.
4. **Code samples:** for each ticket, one run that followed the stale fact and one that didn't.
5. **Tokens, cost and time** per arm and ticket, as a chart and a table; cost per fully correct change.
6. **Robustness:** a second judge (`anthropic/claude-sonnet-5.5`) on the conflict-reported verdicts; the analysis with
   *other* outcomes counted as stale.

## Size and cost

6 arms × 3 tickets × 8 repetitions = **144 runs**, at about $0.10 and 80 s each in OKC: about $15 of model use and
about 4 hours with three runs in parallel. Judging the summaries: a few dollars.

## Pilot (before the main run)

2 runs each of B and E on each ticket (12 runs), plus the hidden tests run against a reference solution and a
stale-following solution for each ticket. The pilot checks the harness, the hidden tests and the stale detectors. It
does not tune where the truth is or how visible the contracts are: if B already catches the stale facts in the pilot,
that is a result, and the main run goes ahead unchanged. If a hidden test or detector is wrong, the fix goes in the
amendment log.

## What it does not show

- One service, written and adapted by me (Claude), with simulated integrations; the bundle, the stale statements and
  the contracts are mine too.
- Three stale facts, each made wrong on purpose and cleanly contradicted by one file. Real staleness is messier:
  partly wrong, in several places, with no contract to check against.
- One agent and model, at one effort level.
- The verify instruction is one wording; others may work better or worse.
- Arm D tests whether the agent acts on freshness metadata, not whether provenance can be trusted.

## After the runs

REPORT.md with impact, risks and configuration recommendations, every table saying what its numbers are and which
direction is better, a token chart, and real artefacts (stale statements, summaries, code) on the site page.

## Amendment log

1. **Build and pilot** (4 November 2026, before the main run). The user's go-ahead: "Yes start".
   - **Build:** the repository, the contracts, the status query, the six arms (generated by `scripts/make_arms.py` from
     OKC's bundle; each passes `check_okf.py --strict`), the stale detectors and the outcome grading as designed. The
     hidden tests were checked against OKC's reference solution for each ticket (outcome *truth*, every test passes),
     a stale-following version of it (outcome *stale*, its detector passes, only the truth tests fail), the untouched
     app (outcome *other*), and for F6 a solution that uses the status query instead of `DUPL` (outcome *truth*, every
     test passes).
   - **Pilot** (12 runs, `results/pilot`): every run built and was graded. B followed the stale fact in 2 of 2 F6 runs
     and got the truth in 2 of 2 F7 and 2 of 2 F3 runs (both F7 runs opened the notification contract on their own);
     E got the truth in all 6. The judge reported a conflict in 1 of 12 summaries; I read all 12 and agree with every
     verdict. Nothing is changed: as the design says, the pilot doesn't tune where the truth is or how visible it is.
   - **Clarification of a measure:** "mentioned freshness" is read from all the agent's messages during the run, not
     only the final summary (the design's "the summary or the agent's messages").
2. **While analysing** (4 November 2026, after the main run; no hypothesis, measure or answer key changed).
   - **One judge verdict overridden** after reading all 144 summaries: F7, D, run 2 says "not deprecated
     `PAYMENT_DECLINED`" without saying the bundle is wrong, so it is not a reported conflict
     (`results/main/judge-overrides.json`). The second judge already said so.
   - **"Mentioned freshness"** as built also matched "Verified with `mvn` …" in ordinary summaries. The report gives a
     strict count alongside it (the bundle's dates, `stale_after`, "out of date", "outdated", "stale OKF/bundle/doc/
     note/guidance/knowledge" in any agent message): A, B, D, F and V 0 of 24, E 8 of 24.
   - **Diagrams** made by `scripts/diagrams.py` (colours checked for colour-blind separation).
3. **After publication** (4 November 2026). The user shared an external review ("Some feedback"). Applied to
   REPORT.md: the verify line's evidence rests on the timeout ticket (0 of 8, 95% upper bound 37%, beside the pooled
   0 of 24 and 14%); H1's zero-width interval explained as complete separation; the date finding worded as "expiry
   metadata without an instruction or enforcement mechanism did not change behaviour"; the verify line's four parts
   (verify, where to look, precedence, report) and the source-of-truth hierarchy added to the limits and
   recommendations; "no run asked" qualified (one-turn runs, nobody to answer); the passing-tests finding promoted;
   the reviewer's next experiment (generic verify against a named source against an enforced check, several tasks)
   added. No hypothesis, measure or number changed.
