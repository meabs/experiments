# Does a curated OKF context layer help an agent that can already read the repo? Report

4 November 2026. Design: [README.md](README.md), pushed before any measured run (e3d8458e). The build, the pilot and
amendments 1 to 10 were pushed before the main run (9d1069e1); amendments 11 to 18 were made afterwards, while analysing,
and none changes a hypothesis, a measure or the answer key. Full numbers: [results/main/analysis.md](results/main/analysis.md).
Hand-check overrides: [results/main/judge-overrides.json](results/main/judge-overrides.json). Failure taxonomy:
[results/main/taxonomy.md](results/main/taxonomy.md).

## 1. What I wanted to find out

A colleague asked whether an **Open Knowledge Format (OKF)** bundle (a few short, structured files describing what a
system is, how it is built and what world it sits in) helps a coding agent that can already read the whole repository.
Earlier OKF experiments here used questions the code could answer. This one asks about the knowledge the code can't
give: the **behaviour of the external systems** a service talks to, and the **service's role** for the people and
systems that depend on it.

The test service is a bank's accounts API (Spring Boot, Java 21) that sends payments through a payment scheme, a fraud
screening service, a core ledger and a notification service. Two kinds of task, treated as equals:

- **Feature changes:** five tickets, each graded by hidden tests. Three need only what the code shows (F1 to F3). Two
  need a fact about an external system that is written only in the system context (F6, scheme timeout; F7, notification
  templates).
- **A service FMEA** (failure mode and effects analysis): a table of what can go wrong, its effect on customers and
  dependants, and its severity, occurrence and detection scores. Graded against a 22-entry answer key.

Three arms, the same agent (Codex 0.157.0 with gpt-5.6-luna, medium effort, web search off) and the same repository:

| Arm | What the agent gets besides the code |
| --- | --- |
| A, vanilla | nothing |
| B, OKF | an `okf/` bundle (four files, about 2,000 words) and a one-line pointer to it in AGENTS.md |
| C, AGENTS.md | the same facts as a plain section of AGENTS.md (which Codex loads into the prompt itself) |

25 runs per arm of each task type: 150 runs.

## 2. Why I thought it was worth testing

An agent reading a payments service can see that it calls a scheme and a ledger, but not that the scheme answers
`DUPL` to a reference it already has, that a ledger timeout may already have booked the posting, or that finance
reconciles every morning at 07:00. Those facts live in a team's heads or a wiki. If a small, structured bundle carries
them to the agent, it should matter most where the code is silent; if the agent can work them out from the code, the
bundle is overhead.

## 3. What I predicted

**The user's prediction** (3 November 2026, quoted): "my assumption that the feature changes will be equal while the
fmea will be better with okf". Fixed before any run:

| # | Statement |
| --- | --- |
| H1 | Feature changes: B's and A's pass rates are within 15 points (equivalence test) |
| H2 | FMEA: B's reports recall more of the answer key than A's |
| H3 | OKF's benefit is larger for the FMEA than for features |
| H4 | B's FMEAs contain fewer invented facts than A's |
| H5 | B and C differ (format against plain text, same facts), for features and for the FMEA |
| H6 | B's advantage over A is larger on context-only answer-key entries than on in-code ones |
| H7 | B's advantage over A is larger on entries about the service's **role** than on its **internals** |

## 4. How I tested it

- **Repository:** written for the experiment, with the integrations as in-process fakes in tests that behave like
  the real systems in the context (for example the fake scheme remembers references and answers `DUPL` to a repeat).
  34 existing tests.
- **Bundle:** written from the code and a wiki-style system context before the tickets, and checked with OKF's
  `check_okf.py --strict`. Arm C's AGENTS.md section is generated from the same text.
- **Pilot first.** The first two integration tickets (F4 fraud screening, F5 ledger retry) hit the ceiling: vanilla got
  all 10 runs right, because the code gave the rules away. The user chose to replace them ("Replace F4/F5
  (Recommended)"). The replacements, F6 and F7, were re-piloted: vanilla failed the integration rule in all 4 runs and
  OKF passed both (amendment 1).
- **Feature grading:** hidden tests per ticket (`functional_`, `access_`, `integration_`), plus all 34 existing tests;
  protected files restored before grading. A run is correct only if every test passes.
- **FMEA grading:** a judge model from another provider (primary `google/gemini-4-argon`) matched each report to the
  answer key, leniently (same failure mode) and strictly (same mode and cause), and listed invented facts. I checked
  it by hand (amendment 12): every positive's matched row title (1,228), about 250 doubtful rows in full, and a random
  fifth of negatives; 24 positives and 2 negatives corrected, 10 of 16 "invented facts" removed. A second judge
  (`anthropic/claude-sonnet-5.5`) graded 40 of the 75 reports before the judging credit ran out (amendment 11).
- **Statistics:** permutation tests (10,000, seed 1), bootstrap intervals, Holm correction across H2 to H7; H1 is a
  two-one-sided equivalence test on a 90% interval resampling tickets, then runs.

## 5. What happened

### Headline

| Arm | Feature changes fully correct (share of 25 runs; higher is better) | FMEA recall (share of the 22 answer-key entries found, mean per report; higher is better) | Invented facts per FMEA (mean; lower is better) |
| --- | --- | --- | --- |
| A, vanilla | 64% (16/25) | 62% | 0.16 |
| B, OKF | **100%** (25/25) | 77% | 0.00 |
| C, AGENTS.md | 92% (23/25) | **81%** | 0.08 |

### Hypotheses

Differences are B − A in percentage points unless stated. H2 to H7 are Holm-adjusted together.

| # | Observed | Interval | Holm p | Verdict |
| --- | --- | --- | --- | --- |
| H1 features within ±15 points | +36 points | 90% CI 0 to +72 | (equivalence test) | **inconclusive**: not shown equal, and the interval reaches 0 |
| H2 FMEA recall B > A | +15 points | 95% CI +11 to +19 | 0.0007 | **supported** |
| H3 benefit larger for FMEA than features | −21 points (the feature gain was larger) | | 0.98 | not supported |
| H4 fewer invented facts with B | 0.16 fewer per report | | 0.22 | not supported (few in any arm) |
| H5 features, B vs C | C − B −8 points | | 0.98 | not supported |
| H5 FMEA, B vs C | C − B +4 points | | 0.30 | not supported |
| H6 bigger gain on context-only entries | +61 points | | 0.0007 | **supported** |
| H7 bigger gain on role entries | +34 points | | 0.0007 | **supported** |

The user's prediction holds for the FMEA (H2). For the features it depends entirely on the ticket: equal on every
ticket whose rules are in the code, and far apart on the two whose rules aren't (next section). The headline +36 points
is an average of those two situations, and the design's equivalence test, which resamples the five tickets, can't call
it either way.

### Feature changes

Fully correct runs per ticket, of 5 (higher is better):

| Ticket | Where the rule is | A | B | C |
| --- | --- | --- | --- | --- |
| F1 list an account's payments | in code | 5 | 5 | 5 |
| F2 cancel a queued payment | in code | 5 | 5 | 5 |
| F3 today's spend against the daily limit | in code | 5 | 5 | 5 |
| F6 keep and resubmit a payment after a scheme timeout | context only | **1** | 5 | 3 |
| F7 notify queued and rejected payments | context only | **0** | 5 | 5 |

- **In-code tickets:** all 45 runs correct, every arm. B − A = 0, with a 90% interval of 0 to 0.
- **Context tickets:** integration rule right in A 1/10, B 10/10, C 8/10 runs (B − A +90 points, 90% interval +70 to
  +100).
- **Every one of the 11 failures** built, passed all 34 existing tests and the ticket's own functional tests, and broke
  only the integration rule. The judge labeller and I agreed on every label (taxonomy: [results/main/taxonomy.md](results/main/taxonomy.md)):
  - **F6, 6 runs (A 4, C 2):** the run resubmits with the same reference, as it should, but then treats the scheme's
    `DUPL` answer (the scheme already has that instruction) as a refusal, and marks the payment `REJECTED`. In a real
    bank the payee has been paid, the customer was never debited, nothing is posted to the ledger, and the customer is
    told nothing; finance's 07:00 reconciliation finds a payment sent but not posted. B's bundle and C's AGENTS.md
    contain the same sentence about `DUPL`; every B run handled it, two C runs did not.
  - **F7, 5 runs (all A):** the run invents the template name `PAYMENT_REJECTED`; the notification service's template
    is `PAYMENT_FAILED`. Every A run guessed the same name, and every summary stated it as fact, with no caveat.
- **Code size** (*exploratory*): median lines added A 29, B 41, C 31; runs that added tests A 4/25, B 11/25, C 8/25.

### Service FMEA

Recall, mean per report (lowest and highest report in brackets; higher is better):

| Answer-key entries | A | B | C |
| --- | --- | --- | --- |
| all 22, lenient | 62% (50–77) | 77% (64–91) | 81% (64–95) |
| all 22, strict (same cause too) | 56% | 73% | 77% |
| 7 context-only | **17%** (0–43) | 70% (43–100) | 72% (43–100) |
| 5 inferable | 83% | 92% | 97% |
| 10 in code | **82%** | 74% | 78% |
| 14 about the service's role | 54% | 81% | 81% |
| 8 about internals | 76% | 70% | 80% |
| 12 high-severity (S ≥ 8) | 59% | 77% | 79% |

Where the context made the difference: reports containing each entry, of 25 (higher is better):

| Entry | Source | A | B | C |
| --- | --- | --- | --- | --- |
| K10 an account is closed with money still in it | context | 0 | 25 | 25 |
| K12 statements wrong or missing (the regulatory return is built from them) | context | 3 | 23 | 23 |
| K11 payments decided against an out-of-date balance | context | 8 | 25 | 24 |
| K01 a payment booked twice in the ledger | context | 15 | 25 | 25 |
| K06 payments queued for a bank holiday are rejected | inferable | 14 | 25 | 25 |
| K08 a notification contains a full account number | context | 0 | 13 | 9 |
| K05 a fraud REFER treated as a rejection | context | 0 | 5 | 8 |
| K04 unscreened payment when fraud screening is slow or down | context | 4 | 6 | 12 |

Where the context cost something (*exploratory*, added after seeing the results; amendment 14):

| Entry | Source | A | B | C |
| --- | --- | --- | --- | --- |
| K21 data lost on restart (in-memory database) | in code | 25 | 19 | 20 |
| K22 every call refused (identity key change) | in code | 20 | 13 | 11 |
| K14 a client retry creates a second payment | in code | 21 | 18 | 20 |

On the 10 in-code entries, B found 8 points fewer than A (95% interval −13 to −3; two-sided p = 0.005, not
Holm-adjusted); 7 of the 10 entries went down and none up. C was 4 points below A (−9 to +1; p = 0.16). A also wrote
more valid failure modes the key doesn't contain (3.2 per report, against B 1.5 and C 2.7; the judge's verdicts, not
hand-checked), mostly code-level: notifications with no timeout, a queued payment dispatched twice by two instances,
a race on closure requests.

Quality of what was found (share of matched entries; higher is better): effects on customers right in 96% (A) to 99%
(C); dependants named 76% of the key's (A), 86% (B), 84% (C). Rank correlation between a report's risk scores and the
key's (1 = same order; higher is better): A 0.39, B 0.50, C 0.58.

Invented facts were rare: 4 in 25 A reports (for example "the scheme has no idempotency contract", where the context
says the reference is unique for 30 days), none in B, 2 in one C report (audit logs the code doesn't have).

### How the agent used the context

- **B opened the bundle in every run (50 of 50)**, as its first command, and read all four files in 48 (two feature
  runs skipped `system.md`). It still opened about as many source files as A (14 against 15 per FMEA): the bundle
  added to the exploration rather than replacing it.
- **Facts reached the work** (FMEA reports containing the fact, of 25; A can only have them from the code or a guess):

| Fact | A | B | C |
| --- | --- | --- | --- |
| fraud policy FRD-7 | 0 | 23 | 23 |
| balance copy overwritten at 02:00 | 0 | 25 | 17 |
| scheme reason code DT01 (invalid date) | 0 | 25 | 25 |
| finance reconciliation at 07:00 | 0 | 23 | 13 |
| fraud review within four hours | 0 | 7 | 3 |

### Consistency, cost and value

- **Consistency:** B was the only arm where every ticket's 5 runs agreed. FMEA recall spread (standard deviation over
  reports; lower is steadier): A 6.6, B 7.1, C 7.0 points.
- **Cost** (list price per run; lower is better):

| Task | A | B | C |
| --- | --- | --- | --- |
| feature change | $0.094 (74 s) | $0.124 (91 s) | $0.100 (74 s) |
| per fully correct feature change | $0.147 | $0.124 | **$0.109** |
| FMEA | $0.154 | $0.145 | $0.149 |
| per answer-key entry found | $0.011 | $0.009 | **$0.008** |

  B's feature runs cost about 32% more than A's (reading the bundle: 352k input tokens against 232k); C's cost 6% more.
- **Payback** (an estimate on a stated assumption, amendment 17): if a person takes about 4 hours to write and review
  a bundle like this, and an integration bug that passes every test costs at least an hour to find and fix, the bundle
  pays back after about 5 tickets that touch an external system's behaviour (it prevented 0.9 such bugs per ticket
  here). Run cost is negligible beside that: a few cents.

### Robustness

- **Second judge** (40 reports: 23 A, 10 B, 7 C): recall A 61%, B 76%, C 82%; B − A +15 points (p = 0.0001). It agreed
  with the primary judge on 850 of 880 found / not-found decisions (97%). On its subset, in-code recall was A 80%, B 74%,
  C 80%, and the same entries dropped (K21: A 23/23, B 6/10; K22: A 19/23, B 5/10).
- **Strict matching** gives the same ordering (56%, 73%, 77%).
- **Entry-level check** (each answer-key entry as the unit, in place of the planned mixed model, amendment 13): B − A
  +15 points over the 22 entries (95% interval +2 to +30); on the 7 context-only entries all 7 went up; on the 10 in-code
  entries 7 went down, none up.
- **Ticket mix:** H1 on the in-code tickets alone: B − A 0 (interval 0 to 0); on the integration tickets alone: +90
  (+70 to +100).

### Case studies

- **F7, the clearest difference.** With only `PAYMENT_SENT` in the code to go on, all five A runs wrote
  `PAYMENT_QUEUED` (right, by luck) and `PAYMENT_REJECTED` (wrong). Each summary reports the names as done work. All
  five B runs opened `okf/architecture.md`, which lists the four templates, and used `PAYMENT_FAILED`.
- **F6, the same facts in two formats.** B/1's summary: "Handles idempotent `DUPL` responses after a scheme accepted a
  timed-out request." C/2's summary: "Retries reuse the existing `P{id}` scheme reference": right, but its code then
  sends `DUPL` down the ordinary rejection path. Both had the sentence; one used it.
- **FMEA, worst and best.** The worst A report (A/11, 11 of 22) missed all 7 context-only entries and 2 inferable
  ones; it covered most of the code (restart data loss, concurrency, tenant isolation). The best reports (C/9, 21 of 22;
  B/12 and B/13, 20) combined both. The worst B report (B/9, 14) found the context entries but missed four in-code ones
  (duplicate client payments, unauthorised payment, restart data loss, every call refused): the crowding-out pattern in
  one report.

## 6. What surprised me

- **The features weren't equal, but only because of the tickets.** With no context, the agent never got an external
  system's convention right unless the code showed it (1 of 10). It didn't flag the guesses either. Where the code did
  show it (the pilot's F4 and F5), vanilla was perfect.
- **Plain AGENTS.md did as well as OKF on the FMEA**, and was cheaper. The format didn't matter there; the facts did.
- **The bundle crowded out code-level failure modes.** The report length stayed about the same (about 16 rows), so
  the context-only entries B added took the place of in-code entries A had found.
- **`DUPL` in the prompt wasn't enough twice.** C had the sentence in its prompt from the start and still mishandled it
  in 2 of 5 runs; B, which opened the file for the task, handled it every time. With 5 runs that is not a significant
  difference (H5).

## 7. What this might mean in practice

### Impact

- For an agent changing code that talks to external systems, **the dangerous gap is the one the tests can't see**:
  every failed change here passed every existing test. In a payments service those were money-moving errors (a payment
  sent and never debited or posted; a customer notification sent under a template name that
  doesn't exist). Putting the external systems'
  conventions where the agent reads them closed that gap on these tickets (A 1/10 right, B 10/10, C 8/10).
- For risk work such as an FMEA, the context changes **what kind** of analysis you get: about the service's role
  (closures, statements, reconciliation, regulators) rather than only its code. Recall on the role entries went from 54%
  to 81%.
- Where the rules are in the code, the context added nothing measurable and cost a little.

### Configuration recommendations

For Codex with gpt-5.6-luna on a repository like this one (the configuration tested):

1. **Write down each external system's conventions** (reason codes, idempotency keys and how long they last, what a
   timeout means, template names, data rules) in a file the agent reads. Either an AGENTS.md section or an OKF bundle
   worked; AGENTS.md was cheaper per correct result in both task types.
2. **Turn those facts into contract tests** where possible (for example "a `DUPL` on resubmission completes the
   payment"). The failures here were invisible to the existing tests, and an agent's confident summary is not a check.
3. **For an FMEA or risk review with context, ask for the code-level checks explicitly** (persistence, authentication
   outages, client retries, concurrency), or review a context run alongside a code-only one. With context, those
   entries were found less often. That either fix works is untested.
4. **Don't expect the format to do the work.** OKF and plain AGENTS.md weren't distinguishable here; choose by what a
   team will keep up to date.

### Risks this exposes

- **Silent, plausible integration errors** when the context is missing: the code builds, tests pass, the summary says
  done, and the external system's rule is broken.
- **Attention is finite.** Adding context shifted the FMEA towards the service's role and away from its internals; a
  reviewer who assumes "more context, strictly better" would miss that.
- **Stale context** was not tested. A bundle that is wrong about a reason code would presumably be followed as
  faithfully as this one was (B used `PAYMENT_FAILED` in every run); earlier OKF work here found stale facts repeated.
- **Having a fact in context isn't the same as using it** (C's two `DUPL` failures).

## 8. What the experiment does not prove

- One repository, written by me (Claude) for this test, with simulated integrations; the bundle and the answer key are
  also mine, and I did the hand check. A real bank system is bigger and messier, and a team's bundle may be better or
  worse.
- One agent and model at one effort level.
- Five feature tickets, two of them chosen (after a pilot) because the code doesn't give their rules away. The feature
  result describes tickets like those, not a typical backlog.
- No equivalence was shown anywhere: B against C, and the in-code tickets, are "no difference found", not "equal".
- The second judge covered 40 of 75 reports; the "extra failure modes" verdicts were not hand-checked.
- The bundle's authoring time was not measured (written by me in minutes); the payback figure rests on an assumption.

## 9. What I'd test next

- **Stale context:** the same bundle with three facts made wrong, to measure how often the agent follows the wrong
  fact over the code.
- **A combined FMEA prompt:** context plus an explicit code-level checklist, to see if it keeps both halves.
- **A bigger, real service** with a team-written bundle, and a stronger model.

## 10. How to reproduce the results

```
cd 2026-11-okf-context
bash scripts/run_all.sh                                   # 150 runs into results/main (needs a Codex login)
python3 -I scripts/judge.py results/main                  # primary judge (OpenRouter key in ~/.config/openrouter.key)
python3 -I scripts/judge.py results/main --judge anthropic/claude-sonnet-5.5
python3 -I scripts/transcripts.py results/main
python3 -I scripts/taxonomy.py results/main
python3 -I scripts/analyse.py results/main --second anthropic/claude-sonnet-5.5
```

The judges' outputs, my overrides, the transcripts summary and every run's diff, grade and FMEA are in `results/main`.
Raw agent transcripts are not published.

## 11. What changed from the design

All amendments are in the [README's amendment log](README.md#amendment-log). Before the main run: F4 and F5 replaced
by F6 and F7 (the user's choice), the fakes, the network and AGENTS.md loading, the judges, K03 re-tagged. After it:
the second judge on a subset (credit), the hand check as done, mixed models replaced by an entry-level check, an
exploratory section added, an H5 display bug fixed, my pilot description of F6's failure corrected, and the payback
assumption.
