# Does a curated OKF context layer help an agent that can already read the repo?

**Status:** design, pre-registered 3 November 2026 (pushed before any measured run). Later changes go in the
[amendment log](#amendment-log).

## Why

Earlier experiments here (OKL, H1, H2) gave the agent an Open Knowledge Format (OKF) guide to a repository it **could
not read**, and the guide made the difference (OKL: 20 of 20 changes passed with the guide, 4 of 20 without). That is
the easy case for a guide.

The everyday case is different. A team adds a small, hand-curated OKF bundle to its **own** repository, which the agent
can read anyway. The bundle records only what the code doesn't say well: the key facts and pitfalls of the repo, the
external systems it integrates with and how they behave, and the business processes the code supports. Is that worth
writing and maintaining, and for which kinds of work?

## Scope

The scope (3 November 2026): a repo with an OKF bundle that documents only the key information and challenges of the
repo and its system context (the external systems it integrates with and the business processes it supports), and the
same repo without it; the agent does two kinds of task on each with the same configuration, a new feature (a technical
change) and an FMEA report (a detailed understanding task); the model is Luna; the runs are automated; the findings
are shared.

How this design meets it:

| Scope item | In this design |
| --- | --- |
| OKF-enabled repo: only key information and challenges, plus system context (external systems, business processes) | Arm B: a curated OKF bundle under a size cap with three parts: system information (incl. key pitfalls), architecture (components and the four external integrations) and system context (what the service does, its business processes, who depends on it) |
| Vanilla repo | Arm A: the same code with no bundle |
| Introduce a new feature (technical change) | Five feature tickets, graded by hidden tests |
| Generate an FMEA report (detailed understanding task) | A service-level FMEA: the accounts service and the role it plays in the bank's wider system, graded against an answer key written before any run. This is the test of whether OKF helps with work other than building |
| Same config for both scenarios | One agent configuration for every arm and task |
| Luna model | `gpt-5.6-luna` |
| Automated | Every run, grade and judgement is scripted |
| Share the findings | REPORT.md and a site page |

Added beyond the scope, with the user's agreement (3 November 2026, "A, B and C"): **arm C**, the same facts as a plain
AGENTS.md section, to tell the format apart from the facts. Not in this run: Cursor (planned for later, subject to governance), so the agent
here is Codex CLI with the same model.

## Terms

- **OKF (Open Knowledge Format):** a folder of short markdown files describing a codebase in a fixed structure (the
  spec: GoogleCloudPlatform/open-knowledge-format, as used in OKL).
- **System context:** facts about the world around the code: the external systems it calls, their rules and failure
  behaviour (cut-off times, timeouts, retry rules, error codes), and the business process each piece of code serves.
- **FMEA (failure mode and effects analysis):** a structured list of the ways a service or process can fail, the effect of each
  failure, its cause, how it would be detected, and how serious it is.

## Questions

1. Does a curated OKF bundle raise the share of feature changes that are correct, including the parts that depend on
   how external systems behave?
2. Does it help with understanding work, not just building? In a service-level FMEA, does the agent find more of the
   real failure modes, describe their effect on customers and other systems correctly, and invent fewer facts?
3. Is any benefit from the **content** (the facts) or from the **OKF format**? The same facts in a plain AGENTS.md
   answer that.
4. Does the benefit come from facts the code can't show (system context), rather than facts the agent could have found
   by reading the code?
5. What does it cost: tokens, time, and the effort of writing the bundle?

## The repository

**SEC-1's Spring Boot accounts API** (accounts, customers, statements, closures; used in SEC-1 and BRK), extended with
four external integrations, each a client interface with a local stub server so tests run offline:

| Integration | What the code shows | What only the system context says (examples) |
| --- | --- | --- |
| Payment scheme | a client that submits payments; a config value `scheme.cutoff=15:30` | payments after the cut-off must be queued for the next working day, not rejected |
| Fraud screening | a client returning `ACCEPT`, `REFER`, `REJECT` | `REFER` holds the payment for a person to review; it is not a rejection |
| Core ledger | a posting client taking a request id | postings must reuse the request's idempotency key; a retry with a new key double-posts |
| Customer notifications | a client sending messages | notifications must never contain a full account number |

A realistic vanilla repo has traces of these rules (a config value, an enum, a field name) but not the rules themselves.
Every fact a task depends on is classified **before any run**:
- **in code:** stated in the code or its comments;
- **inferable:** a diligent reader of the code could work it out;
- **context only:** written only in the system context.

### What the OKF bundle contains

Three kinds of knowledge, kept short (about 3,000 words in all), and no file-by-file description of the code:

| File | Contents |
| --- | --- |
| `okf/system.md` | **System information:** what the service is, who owns it, how it is built, run and tested; its key pitfalls ("challenges") |
| `okf/architecture.md` | **Architecture:** its components and the external systems it connects to, with a diagram; for each integration, the protocol, the rules and the failure behaviour (timeouts, retries, error codes, idempotency) |
| `okf/context.md` | **System context, what it does:** the service's role in the bank, the business processes it supports end to end (paying a bill, getting a statement, closing an account), who depends on it (channels, finance reconciliation, the fraud team, regulatory reporting, complaints) and what each needs from it |
| `okf/index.md` | the OKF bundle index: what each file covers and when to read it |

An example of `okf/context.md` (an excerpt; the real file is written before the tasks):

> **What the accounts service does.** It is the bank's system of record for customers' current-account view: balances,
> statements, account notes and closures. Customers reach it through the mobile app and online banking; it does not
> hold the money itself, which lives in the core ledger.
>
> **Business process: paying a bill.** The customer enters a payment in the app. The accounts service checks the
> balance, asks the fraud service to screen it (`ACCEPT`, `REFER` or `REJECT`), sends accepted payments to the payment
> scheme and posts them to the core ledger. `REFER` means the payment is held for the fraud team to review within four
> hours; it is not a rejection. Payments received after the scheme's 15:30 cut-off are queued for the next working day.
>
> **Who depends on it.** Finance reconciles the ledger against the scheme every morning; a payment posted twice breaks
> reconciliation. The monthly regulatory return is built from statements. The complaints team reads account notes.
>
> **Rules that come from outside the code.** Screening fails closed: if the fraud service doesn't answer within
> 2 seconds, the payment is held, never sent. Ledger postings must reuse the request's idempotency key. Customer
> notifications never contain a full account number.

### Order of work, to keep the bundle from being tuned to the tasks

1. Write the system context (integrations, business processes) as a short internal-wiki-style document, and commit it.
2. Write the OKF bundle from the code and that document, under a size cap (about 3,000 words), and commit it.
3. Only then write the tasks and their hidden tests and answer keys.

I write all three, so the bundle may still suit the tasks better than a real team's would; the report will say so.

## Arms (same agent, same configuration, differing only in files)

| Arm | What the repository contains |
| --- | --- |
| **A. Vanilla** | the code, its tests and a minimal README |
| **B. OKF** | A plus the curated OKF bundle (`okf/`: system information, architecture, system context; see above), and one line in AGENTS.md pointing to it |
| **C. Same facts, plain** | A plus the same facts as B, word for word where possible, as a single AGENTS.md section, no OKF structure |

C is the control for "is it the format or the facts?". If B and C score the same, a team can get the benefit without
adopting the format.

## Tasks

Written as tickets, not as instructions: no ticket restates a rule from the system context.

The two task types are treated as **equals**: the same number of runs per arm (25 each), a per-run score on the same
0–1 scale, the same tests, and results reported side by side. Neither is pooled into the other.

- **Feature tickets (5 tickets × 5 runs per arm; F4 and F5 replaced by F6 and F7, amendment 1):** ordinary feature work on the service, as a team would get it.
  The mix is fixed before any run: **three** tickets whose rules are all in the code, and **two** that touch an external
  system's behaviour (for example, "Let customers schedule a payment for later today", which crosses the scheme's
  cut-off). Graded by **hidden tests** run after the agent finishes: the ticket's behaviour, any integration rule, and
  the existing test suite. Score: 1 if every hidden test passes, else 0. Results are also reported per ticket, so a
  difference can be traced to the tickets that cause it.
- **Service FMEA (1 task × 25 runs per arm):** an FMEA of the accounts service as a part of the bank's wider system. The task
  is about the service's role, not the internals of one code path: what the service does for the business, what it
  depends on, who depends on it, and what happens to customers, colleagues and other systems when any part fails. The
  prompt (as a request a team lead might send):

  > We're reviewing the operational risk of the accounts service before the next release. Produce an FMEA for the
  > service: for each way it can fail, give the failure mode, its cause, the effect on customers and on the systems and
  > teams that depend on it, how we would detect it, a severity, occurrence and detection score from 1 to 10 and the
  > resulting risk priority number, and a recommended action. Write it to `docs/fmea.md`.

  Graded against an **answer key** written before any run (see the example below). Each key entry is tagged with where
  the knowledge lives (in code, inferable, context only) and whether it concerns the service's **role** (upstream and
  downstream effects, business process) or its **internals**.

### What the service FMEA's answer key looks like (example entries)

The system context describes the service's place in the bank, for example: *the accounts service sits between the
mobile and online banking channels and core banking. It gives customers their balances and statements, takes payment
instructions, screens them with the fraud service, sends them to the payment scheme and posts them to the core ledger.
Statements also feed the monthly regulatory return; the complaints team reads account notes.*

| Failure mode | Cause | Effect on customers and dependent systems | Detection | S / O / D | Source | About |
| --- | --- | --- | --- | --- | --- | --- |
| A payment is posted to the ledger twice | a retry after a ledger timeout sends a new idempotency key | customer debited twice; ledger and scheme don't reconcile; finance's end-of-day reconciliation breaks | reconciliation mismatch next morning; customer complaint | 9 / 4 / 6 | context only (the ledger's idempotency rule) | role |
| A payment submitted after 15:30 is rejected instead of queued | the cut-off is treated as an error | customer's bill goes unpaid, late fees; complaints volume rises | customer complaint only | 7 / 5 / 7 | inferable (`scheme.cutoff` in config) | role |
| A fraud `REFER` is treated as `REJECT` | the client maps every non-`ACCEPT` to failure | genuine payments refused; fraud team's review queue is never used | rise in failed payments; fraud team sees an empty queue | 6 / 4 / 6 | context only (what `REFER` means) | role |
| Fraud service times out and the payment goes through unscreened | the client fails open on timeout | fraud losses; breach of the screening policy | not detected without a timeout metric | 10 / 2 / 9 | context only (the bank's fail-closed policy) | role |
| A notification contains a full account number | the message template uses the raw field | data protection breach; regulator notification | DLP scan or customer report | 8 / 3 / 7 | context only (masking rule) | role |
| A statement omits pending transactions | the query filters on posted status only | customer sees a wrong balance; the regulatory return is understated | customer complaint; return validation | 7 / 3 / 6 | in code | internals |
| An account is closed with a non-zero balance | the closure check reads a cached balance | customer funds stranded; manual remediation by operations | operations' daily exceptions report | 8 / 2 / 5 | in code | internals |

The real key will have about 20 entries, roughly half of them about the service's role. Scores in the key are a guide
for the judge, not a target: the measures below don't require the agent's numbers to match.

## Agent

Codex CLI with hosted `gpt-5.6-luna` at medium effort, one turn per run, nobody to ask, in a bubblewrap sandbox with no
network. The hidden tests and answer keys aren't in the sandbox. A Cursor repeat is planned later; the arms, tasks
and graders are designed to carry over.

## Measures

- **Feature correctness** (higher is better): hidden tests pass, per run. Also, separately, whether the
  **integration rule** is right.
- **FMEA recall** (higher is better): share of the answer key's failure modes found, overall, by source (in code,
  inferable, context only), for **role** entries against **internals** entries, and for the high-severity ones.
- **FMEA effects correct** (higher is better): for each failure mode found, whether its stated effect on customers and
  dependent systems matches the key (for example, naming reconciliation, the fraud team or the regulatory return).
- **Invented facts** (lower is better): claims about external systems or business rules that are in neither the code
  nor the system context. A run that confidently invents a cut-off time or an error code is worse than one that says it
  doesn't know.
- **Use of the context:** whether the run opened the bundle or AGENTS.md section (from the transcript).
- **Cost:** tokens (input, cached, output, reasoning), wall time, list-price cost; plus the time it took to write the
  bundle.

FMEA reports are matched to the answer key by a judge model from another provider; I check every match the judge makes
in the pilot, and every positive plus a random fifth of negatives in the main run.

## Prediction and hypotheses (fixed before the runs)

**The user's prediction** (3 November 2026): "my assumption that the feature changes will be equal while the fmea will be
better with okf". The first two hypotheses test exactly that; the rest explain it.

| # | Statement | How it is judged |
| --- | --- | --- |
| H1 | **Feature changes: OKF makes no practical difference.** B's and A's feature pass rates are within 15 points | equivalence: the 90% bootstrap interval of B − A (resampling tickets, then runs) lies inside ±15 points (two one-sided tests at 5%) |
| H2 | **FMEA: OKF is better.** B's service FMEAs recall more of the answer key than A's | one-sided permutation test over runs |
| H3 | OKF's benefit is larger for the FMEA than for features | permutation test on the difference of differences, (B − A on FMEA recall) − (B − A on feature pass rate), both on a 0–1 scale |
| H4 | B's FMEAs contain fewer invented facts than A's | one-sided permutation test |
| H5 | B and C differ (format against plain text, same facts) | two-sided permutation tests, one for features and one for the FMEA |
| H6 | B's advantage over A is larger on context-only items than on in-code items (feature rules and FMEA entries) | permutation test on the difference of differences |
| H7 | In the FMEA, B's advantage over A is larger on **role** entries than on **internals** entries | permutation test on the difference of differences |

H2 to H7 are Holm-adjusted together at α = 0.05. H1 is an equivalence test and is reported on its own: with 25 runs per
arm it may come out **inconclusive** (the interval too wide to show equivalence or a difference), and the report will say
so rather than read "no difference" as "equal". Bootstrap 95% intervals: 10,000 resamples, seed 1.

## Detailed analysis plan

The hypotheses above give the headline. This experiment also goes deep: every analysis below is written into
`scripts/analyse.py` and dry-run on the pilot **before** the main run. Analyses marked *exploratory* are reported as
such, beside the pre-registered ones, never instead of them.

### 1. Feature changes, in depth

- **Per ticket and per arm:** pass rate with Wilson 95% intervals, and which hidden tests failed.
- **Failure taxonomy** for every failed run, labelled from the diff and transcript into fixed categories: integration
  rule wrong (and which rule), ticket behaviour wrong, existing test broken, incomplete change, wrong file, build
  failure. Two labellers: a judge model and me; disagreements settled by me, agreement reported (Cohen's kappa).
- **By fact type:** pass rate on tickets whose rules are in code, inferable, or context only (H6's feature half).
- **Code quality beyond pass/fail** (*exploratory*): size of the diff, files touched, whether the change adds tests,
  and whether it puts the integration rule in the right component (from the architecture), judged against a reference.
- **Silent wrong assumptions:** runs that pass the ticket but state a wrong fact about an external system in their
  summary or code comments.

### 2. Service FMEA, in depth

- **Recall** against the answer key: overall, by source (in code, inferable, context only), by **role** against
  **internals**, and by severity (the key's high-severity entries reported on their own).
- **Per key entry:** for each of the about 20 failure modes, the share of runs in each arm that found it. This shows
  which knowledge the bundle carried and which the code alone gave away.
- **Quality of each matched entry**, on fixed criteria: the effect on customers is right; the dependent systems and
  teams are named (finance reconciliation, the fraud team, regulatory reporting, complaints, channels); the cause is
  plausible for this code; the detection method exists in this system; the recommended action would address the cause.
- **Scoring sense:** rank correlation (Spearman) between the run's risk priority numbers and the key's, over the matched
  entries: does the agent rank the serious failures as serious?
- **Invented facts**, classified: an invented external system, an invented rule or number (a cut-off time, a timeout),
  a wrong claim about the code, and a contradiction of the system context. Counted per run and per 1,000 words.
- **Extra failure modes** not in the key: each one judged as valid (a real risk the key missed: the key is then
  reported as incomplete, not edited), generic (true of any service), or wrong.
- **Coverage of dependants** (*exploratory*): how many of the service's dependants (customers, channels, finance,
  fraud team, regulator, complaints, operations) each FMEA mentions at all.
- **Structure:** whether every row has all the requested columns, and the report's length.

### 3. How the agent used the context (from the transcripts)

- **Did it read the bundle (B) or the AGENTS.md section (C)?** When in the run, how much of it, and which files.
- **Traceability of facts:** the bundle contains distinctive wording and values (for example "four hours" for a fraud
  review, "2 seconds" for the screening timeout). Each value is searched for in the output, to tell which facts reached
  the work, and whether A runs produced them anyway (from the code) or invented different ones.
- **Exploration:** files opened, searches run, commands, and tokens spent reading before the first edit or the first
  line of the FMEA. Does the bundle replace exploration or add to it?
- **Reading and outcome** (*exploratory*): within B and C, do runs that read more of the context score better?
  Correlation only; reading isn't randomised.

### 4. Format against facts (B against C)

- Every measure above, for B against C. If C matches B, the benefit is the facts, not the OKF structure.
- Whether C runs read their AGENTS.md section as often and as fully as B runs read the bundle.

### 5. Consistency, cost and value

- **Run-to-run consistency:** for each ticket, how often all 5 runs agree; for the FMEA, the spread of recall over 25
  runs and which entries are found only sometimes. Less spread is valuable on its own.
- **Cost:** tokens (input, cached, output, reasoning), wall time and list-price cost, per run and per correct result
  (cost per passed feature; cost per answer-key entry found).
- **Value of the bundle:** the time it took me to write it, recorded as I write it, against the gain per run, to
  estimate when it pays back.

### 6. Robustness checks

- **Second judge:** the FMEA matching is repeated with a judge from a different provider; results under both are
  reported, with their agreement. Every judge match is checked by hand in the pilot; in the main run, every positive and
  a random fifth of negatives.
- **Strict and lenient matching:** FMEA recall computed both ways (strict: same failure mode and cause; lenient: same
  failure mode).
- **Sensitivity to the ticket mix:** H1 recomputed on the three in-code tickets alone and on the two integration
  tickets alone, so readers can see how much the mix decides the answer.
- **A model of the whole data** (*exploratory*): a logistic mixed model for feature passes and a linear mixed model for
  FMEA recall, arm as a fixed effect and ticket as a random effect, as a check that the permutation results hold.

### 7. Case studies

For each task type, the best and worst run in each arm, and one run where A and B differ most on the same ticket, are
written up from the transcript: what the agent read, what it assumed, and what it got right or wrong.

## Size and cost

(5 feature tickets × 5 runs + the service FMEA × 25 runs) × 3 arms = **150 runs**, 75 of each type. Earlier Luna runs on this repository cost about $0.02 a run; FMEA runs read
more and write more, so budget about $15 including the judge.

## Pilot (before the main run)

- Arm A on every task, 2 runs each; arm B, 1 run each; the FMEA 3 times in A and B, to check the answer key
  and the judge before the main run.
- **Ceiling check:** if A already gets the integration rules right on the feature tickets, the context isn't needed
  and the tickets don't test it; I bring that to you before the main run, not after.
- **Floor check:** if B also fails, the ticket or test is wrong.
- Check that the hidden tests and answer keys can't be seen from the sandbox, and that a reference solution passes
  every hidden test.

## What it does not show

- One repository, written by me, with integrations simulated by stubs. A real bank system is bigger and messier.
- A bundle written by me, knowing the kinds of task; a team's bundle may be better or worse.
- One agent and model. Cursor, or a stronger model, may use context differently.
- A fresh bundle. Out-of-date context is a real risk (earlier OKF work found stale facts get repeated) and is a
  proposed follow-up, not part of this run.

## After the runs

REPORT.md in the usual sections (results, impact, risks, configuration recommendations), a site page via PR, and a
YouTube Short in the whiteboard format with the robot, the duck and humour.

## Amendment log

All made on 4 November 2026, after the pilot and **before the main run**. The pilot's runs are not part of the results.

1. **Two feature tickets replaced (ceiling check).** In the pilot, arm A (no context) got all 10 runs of the five
   tickets right, including both integration tickets: F4 (fraud screening), because the unused status
   `HELD_FOR_REVIEW` gave away what `REFER` means, and failing closed is the obvious choice; and F5 (ledger retry),
   because the payment already stores its `ledgerReference`, so reusing it is the natural code. Neither tested the
   context. I put this to the user, who chose (quoted): "Replace F4/F5 (Recommended)". They are replaced by **F6**
   (a scheme timeout: keep the payment and resubmit it; the context says a timeout may mean the scheme took it, that the
   reference must be reused, and that the scheme answers `DUPL` to a reference it already has) and **F7** (notify
   customers of queued and rejected payments; the context gives the notification service's templates and the
   last-four-digits rule). Both rely only on facts already in the system context, which was **not** changed. F6 and F7
   were piloted (arm A twice, arm B once) before the main run. The F4 and F5 pilot results are reported as a finding:
   on these, the code's traces were enough.
2. **Code and test support changed for F6 and F7**, for every arm alike: `SchemeTimeoutException` (the scheme client
   now throws it on a timeout instead of Spring's exception; still not caught, as before); `FakeScheme` behaves like the
   scheme (remembers references, answers `DUPL` to a repeat, can time out before or after taking an instruction);
   `FakeNotifications` can fail. The 34 existing tests pass unchanged.
3. **External systems in tests are in-process fakes** (`TestIntegrations`), not local stub servers as the design said.
4. **Sandbox network.** The sandbox shares the network, because the hosted model needs it; web search is off in every
   arm (`web_search="disabled"`). Nothing else changes ("no network" in the design was wrong).
5. **Codex loads AGENTS.md into the prompt itself.** So arm C always has its section in context; arm B sees the
   one-line pointer and must open `okf/`. "Use of the context" is therefore measured for B only (every pilot B run
   opened all four bundle files first). This is a real difference between the formats, and the report will say so.
6. **The bundle is about 2,000 words** (under the 3,000 cap; it passes OKF's `check_okf.py --strict`). It was written
   by me (Claude) from the code and the system context in a few minutes, so its writing time says nothing about a
   team's effort; the payback analysis (part 5) uses its size and a stated estimate of a person's time instead.
7. **Judges.** Primary `google/gemini-4-argon`, second `anthropic/claude-sonnet-5.5`, both through OpenRouter. After
   the pilot hand check (every match: 86 positives checked, none wrong; one "invented fact" was a recommendation, and is
   overridden), the judge prompt now says that a recommendation or proposed change is not an invented fact.
8. **Answer key: K03 re-tagged** from context only to inferable. In every pilot A run the agent found that payments
   aren't screened, from the unused client in the code; only the policy behind it (FRD-7) is context. The key now has
   7 context-only, 5 inferable and 10 in-code entries. No entry was added, removed or reworded.
9. **H6 made precise.** H6 is tested on the FMEA (recall on context-only entries minus recall on in-code entries,
   B against A). Its feature half is reported in section 1 (in-code tickets F1 to F3 against integration tickets F6 and
   F7) with an interval, outside the Holm family.
10. **Hidden tests** check behaviour, and an external system's names only where they are its interface: F7 checks the
    notification service's template names, which are written in the system context.

### After the main run (4 November 2026)

These were made after the main run had finished, while analysing it. None changes a hypothesis, a measure or the
answer key.

11. **Judge budget.** The OpenRouter credit ran low part-way through judging (two judges in parallel, six requests
    each, hit "would exceed your available credits"). The failed calls were dropped and re-run one at a time
    (`OKFC_JUDGE_WORKERS=1`). The primary judge graded all 75 reports. The **second judge graded 40**: the 23 A reports it
    finished before the credit ran out, plus 10 B and 10 C reports drawn at random (seed 1; `OKFC_JUDGE_RUNS`), of
    which 3 C calls failed when the credit ran out again (10 B and 7 C graded). Its results and its agreement with the
    primary judge are therefore on this subset only.
12. **Hand check of the primary judge, as done.** I read the matched row title of every positive (1,228), read in
    full the row behind every one whose title didn't plainly name the key entry's failure (about 250), and read the
    row text found by a keyword search for a random fifth of negatives (84 of 422, seed 1). 24 positives were wrong and
    are overridden (most: a row about logs or API responses credited as a notification leak, K08; a generic
    notification outage credited as "not told about a rejection", K18; a disclosure-only access row credited as "someone
    else makes a payment", K20); 2 negatives were wrong and are added. All 16 "invented facts" were read: 10 are removed
    (the code does have `Customer.riskScore`; "no approval endpoint" is true of the code; three were recommendations) and
    6 kept. Every override, with its reason, is in `results/main/judge-overrides.json`. The "extra failure modes"
    verdicts (valid, generic, wrong) were not hand-checked and are reported as the judge's.
13. **Mixed models replaced.** The planned logistic and linear mixed models (exploratory) were not fitted: `statsmodels`
    isn't installed (and I ask before installing), and the feature data are completely separated (every run of F1 to
    F3, and every B run, passed), so a logistic model has no finite estimate. In their place, an **entry-level check**:
    each answer-key entry is the unit, resampled over entries, which asks whether the FMEA result holds across failure
    modes rather than across runs.
14. **Exploratory section added after seeing the results** (`analyse.py`, section 6a): two-sided recall differences
    for every pair of arms on in-code, internals and context-only entries. It was added because the pilot hinted that
    the bundle draws attention away from code-level entries; it is labelled exploratory and not Holm-adjusted.
15. **Bug fix in `analyse.py`**: the H5 rows did not receive their Holm-adjusted verdict (a key mismatch); fixed. No
    other number changed.
16. **Correction of how F6's failure was described.** In the pilot notes I wrote that arm A "pays twice after a
    timeout". It doesn't: every run resubmits with the same reference (`integration_resubmitUsesTheSameReference`
    passed in all 15 runs). The failing runs treat the scheme's `DUPL` answer (it already has that instruction) as a
    refusal and mark the payment `REJECTED`. The payee has been paid, but the customer is never debited and nothing is
    posted to the ledger, and the customer is told nothing. Finance's 07:00 reconciliation sees a payment sent but not
    posted.
17. **Payback (part 5)** uses a stated assumption, not a measurement: that a person would take about 4 hours to write
    and review a bundle like this one (amendment 6).
18. **Failure taxonomy**: every failed feature run fell into one category (integration rule wrong), so Cohen's kappa
    on the category is undefined (chance agreement is 100%); the plain agreement (100%) is reported instead. On the rule
    (two values) kappa is 1.00. The judge labeller ran with `max_tokens` 400 to fit the remaining credit.
19. **Scope wording and report content** (4 November 2026, after publication of the first version). The user asked:
    "Can you remove the colleague statement and [I want] some actual samples of the FMEA in the report and also explain
    the changes requested for the features and also the end state OKF structure with samples". The quoted scope message
    is replaced by a summary of its content (the scope itself is unchanged), and REPORT.md gains the ticket texts, the
    bundle's structure with excerpts, and real FMEA rows. No result changes.
20. **Second judge completed** (4 November 2026). After the user topped up the credit ("I added openrouter credits"),
    the second judge graded the remaining 35 reports, so it now covers all 75 (amendment 11 is superseded on coverage).
    All 75: recall A 61%, B 76%, C 80%; agreement with the primary judge 97% (1,597/1,650). On the exploratory in-code
    check it gives B − A −5 points (two-sided p = 0.08), against the primary judge's −8 (p = 0.005).
21. **External review** (4 November 2026). The user shared a reviewer's feedback and asked: "review this feedback and
    see if it changes [your] view". Checked against the files, four points are added to REPORT.md, with no result
    changed: the feature headline depends on two tickets chosen for missing facts; B against C changes format and
    delivery together, so H5 is not a test of OKF's format alone; the bundle's `generated.by: human:accounts-squad` is
    synthetic (I wrote it); and F6 is graded on the simulated contract although the bundle documents a status query. The
    risk "attention is finite" is reworded, because the FMEA prompt set no length and the data fit the agent deciding a
    report is complete just as well. Section 9 gains a format-against-delivery arm and a two-pass FMEA.
22. **Cost correction** (5 November 2026, after publication). The user asked: "Fix OKF cost figures: the okf-context
    and okf-stale reports still show costs about 6 times too high (they used $1.25, $0.125 and $10 per million tokens
    instead of $0.20, $0.02 and $1.20)". The analysis used a wrong list price for gpt-5.6-luna. Re-priced at $0.20 per
    million new input tokens, $0.02 cached and $1.20 output (OpenAI's pricing page, 5 November 2026); the cost per
    answer-key entry is now shown per 1,000 entries, as the per-entry figures round to the same cent fraction. Token
    counts, times, grades and every other number are unchanged. The design's cost estimate (section above) is left as
    written.
