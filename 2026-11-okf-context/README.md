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

The scope is this message (user, 3 November 2026), quoted as written:

> In my own environment create a repo with:
> - OKF Enabled, based on documenting only the key information / challenges of the repo and system context e.g. what
>   it integrates into (external systems) and business processes the code supports
> - Vanila Repo
>
> Then get the agent to do these two types of tasks:
> - Introduce a new feature
> - Generate a FMEA report
>
> The aim is to test two different scenarios with the same config e.g. a technical change and then a detailed
> understanding task, I have a testing framework that allows me to automate these. I will use the Luna model as I need
> to manage usage.
>
> I will then share the findings

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
AGENTS.md section, to tell the format apart from the facts. Not in this run: Cursor (the message says it comes later,
subject to governance), so the agent here is Codex CLI with the same model.

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

- **Feature tickets (5 tickets × 5 runs per arm):** ordinary feature work on the service, as a team would get it.
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
network. The hidden tests and answer keys aren't in the sandbox. The colleague plans to repeat the setup in Cursor later;
the arms, tasks and graders are designed to carry over.

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

(none yet)
