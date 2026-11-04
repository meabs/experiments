# Does a curated OKF context layer help an agent that can already read the repo? Report

4 November 2026. Design: [README.md](README.md), pushed before any measured run (e3d8458e). The build, the pilot and
amendments 1 to 10 were pushed before the main run (9d1069e1); amendments 11 to 18 were made afterwards, while analysing,
and none changes a hypothesis, a measure or the answer key. Full numbers: [results/main/analysis.md](results/main/analysis.md).
Hand-check overrides: [results/main/judge-overrides.json](results/main/judge-overrides.json). Failure taxonomy:
[results/main/taxonomy.md](results/main/taxonomy.md).

## 1. What I wanted to find out

Does an **Open Knowledge Format (OKF)** bundle (a few short, structured files describing what a
system is, how it is built and what world it sits in) help a coding agent that can already read the whole repository?
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
  (`anthropic/claude-sonnet-5.5`) graded all 75 reports (the last 35 after a credit top-up; amendments 11 and 20).
- **Statistics:** permutation tests (10,000, seed 1), bootstrap intervals, Holm correction across H2 to H7; H1 is a
  two-one-sided equivalence test on a 90% interval resampling tickets, then runs.

### The feature tickets

Each ticket was the whole prompt, with the line "Follow the existing conventions (README.md) and keep the existing
behaviour and tests working" at the end. The full texts are in [tasks/](tasks/); the hidden tests in [hidden/](hidden/).

| Ticket | What it asks for | Where the rule that decides it lives | What the hidden tests check |
| --- | --- | --- | --- |
| F1 payment history | `GET /api/accounts/{accountId}/payments`: the account's payments, newest first, with an optional `status` filter (an unknown status gets 400) | the code: the existing payment endpoint and access rules | newest first, filter, 400 on an unknown status, only that account's payments; support staff and admins who look after the account see them, anyone else gets 404 |
| F2 cancel a queued payment | `POST /api/payments/{paymentId}/cancel`: `QUEUED` becomes `CANCELLED` and is never sent; any other status can't be cancelled; holder only | the code: statuses, the queued-payment job, the holder rule | the holder cancels, the payment is never sent, other statuses conflict, only the holder, write scope needed |
| F3 today's allowance | `GET /api/accounts/{accountId}/payment-allowance`: `dailyLimit`, `paidToday`, `remaining` (never below 0), agreeing with the existing limit check | the code: the limit check in `PaymentService` | rejected payments don't count, queued ones count on the day they're made, the UK day boundary, agreement with the limit check, staff access |
| F6 scheme timeout | on `SchemeTimeoutException`, save the payment as `RECEIVED` and answer 201; a `SchemeRetryJob.resubmit()` every 5 minutes resubmits `RECEIVED` payments, which then carry on as normal | **the context only:** the scheme's reference is unique for 30 days and a repeat gets `DUPL`; a timeout may mean the scheme accepted it, so `DUPL` on a resubmission means "already have it", not a refusal | the payment is kept; a resubmission completes it; it **reuses the same reference**; a payment the scheme accepted before timing out is **completed, not rejected or paid twice** |
| F7 notify every outcome | also notify the customer when a payment is queued for a later day and when the scheme rejects it, "as we already do for payments that are sent" | **the context only:** the notification service's template names (`PAYMENT_QUEUED`, `PAYMENT_FAILED`) and the last-four-digits rule; the code only shows `PAYMENT_SENT` | both outcomes notified, still one message for a sent payment, a notification failure doesn't fail the payment; **the service's real template names**; never the full account number |

F4 (fraud screening) and F5 (ledger retry) were written and piloted but dropped at the ceiling (section 4, pilot).

What the difference looked like in the code. F6, the `DUPL` branch an OKF run wrote (B/1, passed):

```java
} catch (SchemeRejectedException e) {
    // A retry after a timeout can discover that the original instruction was
    // accepted. The scheme reference is idempotent, so carry on with the
    // payment rather than treating that discovery as a rejection.
    if (payment.getStatus() == PaymentStatus.RECEIVED && "DUPL".equals(e.getCode())) {
        payment.setExecutionDate(today);
        payment.setStatus(PaymentStatus.SUBMITTED);
    } else {
        payment.setStatus(PaymentStatus.REJECTED);
        ...
```

The vanilla run A/1 caught the timeout and reused the reference correctly, but left the existing rejection handler as
it was, so the resubmission's `DUPL` marked the payment `REJECTED` (failed). F7, vanilla A/1 (failed): it added
`notifyCustomer(account, payment, "PAYMENT_REJECTED", ...)`; the notification service has no such template.

### The OKF bundle (end state)

Arm B's repository had this added (written before the tickets, from the code and a wiki-style system context, and
checked with OKF's `check_okf.py --strict`; files in [arms/B/okf/](arms/B/okf/)):

```
AGENTS.md                 one added line pointing to okf/index.md
okf/
  index.md          150 words   what the bundle is and which file to read for what
  system.md         579 words   what the service is; build, run, test; six key pitfalls
  architecture.md   649 words   components, the payment flow, and each external system's rules and failure behaviour
  context.md        615 words   the service's role in the bank, the business processes, who depends on it
```

Each file starts with OKF front matter (`type`, `title`, `description`, `status`, who wrote it and when, and its
sources). Excerpts, quoted as the agent saw them:

`okf/index.md`:

> - [System information](/system.md) - what the service is, how to build, run and test it, and its key pitfalls. Read
>   before any change.
> - [Architecture](/architecture.md) - components, the payment flow, and each external system's rules and failure
>   behaviour (scheme gateway, fraud screening, core ledger, notifications). Read before touching `payment` or
>   `integration`.
> - [System context](/context.md) - the service's role in the bank, the business processes end to end, who depends on
>   it and what they need. Read for anything about risk, operations or the effect of a change on other teams.

`okf/system.md`, key pitfalls (two of six):

> 1. **The balance here is a copy.** The ledger overwrites `accounts.balance` every night at 02:00; during the day the
>    service debits its own copy. Anything that must be exact (closing an account at zero balance) has to be checked
>    against the ledger, not the copy.
> 2. **The ledger `reference` is an idempotency key.** The ledger books a reference once (a repeat within 24 hours
>    returns the first booking). A ledger **timeout doesn't mean the posting failed**: it may have been booked. Any
>    retry must reuse the payment's original `ledgerReference`; a new reference debits the customer twice.

`okf/architecture.md`, two of the four external systems (the facts F6 and F7 turn on):

> ### Payment scheme gateway
> - **Reference unique for 30 days** (`DUPL` on a repeat). Resending the same reference is safe; a new reference pays
>   twice.
> - **Timeout 10 s.** A timeout may mean accepted. The status query `GET /v2/instructions/{reference}` tells you; the
>   service doesn't use it yet, and doesn't catch the timeout (the request fails and rolls back).
>
> ### Customer notifications
> - Templates: `PAYMENT_SENT`, `PAYMENT_QUEUED`, `PAYMENT_UNDER_REVIEW`, `PAYMENT_FAILED`.
> - **Last four digits only** (`accountEnding`), never a full account number or sort code: a full number is a
>   reportable data-protection breach.
> - **Best effort:** catch and log failures; never fail or undo a payment for one; no retries.

`okf/context.md`, a business process and part of the dependants table (the facts the FMEA's context-only entries need):

> ### Closing an account
> The holder or an admin asks; an approver decides. An account may only be closed at a zero balance, **checked against
> the ledger**; closing with money left in it strands the customer's funds until operations remediate by hand.
>
> | Dependant | What they need |
> | --- | --- |
> | Finance reconciliation | at **07:00** every morning it matches ledger postings to the scheme's settlement report by payment reference; a double posting, or a payment sent but not posted, is a break a person must investigate |
> | Fraud team | held payments, with the screening result, to review within four hours |
> | Regulatory reporting | complete, correct statements for the monthly return |

Arm C got the same text, without front matter or links, as a "System knowledge" section of AGENTS.md (200 lines;
[arms/C/AGENTS.md](arms/C/AGENTS.md)).

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
Holm-adjusted; the second judge gives −5 points, p = 0.08); 7 of the 10 entries went down and none up. C was 4 points below A (−9 to +1; p = 0.16). A also wrote
more valid failure modes the key doesn't contain (3.2 per report, against B 1.5 and C 2.7; the judge's verdicts, not
hand-checked), mostly code-level: notifications with no timeout, a queued payment dispatched twice by two instances,
a race on closure requests.

Quality of what was found (share of matched entries; higher is better): effects on customers right in 96% (A) to 99%
(C); dependants named 76% of the key's (A), 86% (B), 84% (C). Rank correlation between a report's risk scores and the
key's (1 = same order; higher is better): A 0.39, B 0.50, C 0.58.

Invented facts were rare: 4 in 25 A reports (for example "the scheme has no idempotency contract", where the context
says the reference is unique for 30 days), none in B, 2 in one C report (audit logs the code doesn't have).

### Sample FMEA rows

Real rows, quoted as written (from [A/12](results/main/fmea-A/runs/FMEA/A/codex/12/fmea.md) and
[B/12](results/main/fmea-B/runs/FMEA/B/codex/12/fmea.md); the reports had 16 and 18 rows). Scores are the agent's:
S severity, O occurrence, D detection (10 = least likely to be caught), RPN = S × O × D.

**The same failure mode, with and without the context** (key entry K02, scheme timeout). Both found it and scored it
the same; B's row names the 10-second timeout, the unused status query and the `P` reference from the bundle, and
gives a fix that matches the scheme's rules. A's is right but generic.

| Run | Failure mode | Cause | Effect | S/O/D | RPN | Action |
| --- | --- | --- | --- | --- | --- | --- |
| A/12 | Scheme timeout leaves payment outcome ambiguous | `HttpSchemeClient` converts network errors to `SchemeTimeoutException`, but the API has no explicit handler or durable retry/reconciliation state; the gateway may accept before the response is lost | Customer receives a 5xx or sees no usable result; retry can duplicate the transfer, while a successful scheme instruction may be hidden. Scheme and accounts service disagree; operations must search by instruction/reference | 10/4/9 | 360 | Treat submission as an outbox/state machine, use a stable idempotency/reference, map timeout to an explicit pending state, and reconcile unknown outcomes before retrying |
| B/12 | Scheme timeout loses the local payment while the scheme accepted it | A 10-second submit timeout is allowed to escape; the surrounding transaction rolls back, and the service does not query the scheme status | The scheme may send the money while the customer sees an error and no payment record exists locally. The customer may retry and create a second payment; finance and complaints cannot reliably trace it | 10/4/9 | 360 | Persist a `SUBMITTING` record before the call; on timeout query by the stable `P` reference, then reconcile to submitted/rejected/unknown; make retries reuse the same scheme reference |

**A failure mode only the context reveals** (K10; found by 25 of 25 B reports and none of A's). B/12:

| Failure mode | Cause | Effect | S/O/D | RPN | Action |
| --- | --- | --- | --- | --- | --- |
| Account closure proceeds without proving a zero ledger balance | Closure request flow checks only local account status and pending-request state; the required approver/approval and ledger zero-balance operation are not present in the exposed implementation | An account can be closed with money left, stranding customer funds and requiring manual operations remediation. Back office and complaints lose a reliable closure trail | 10/4/8 | 320 | Implement a two-person approval transition that queries the ledger immediately before closure, is idempotent and auditable, and blocks closure on non-zero/unknown balance |

The code alone shows a closure request with a status check; nothing in it says the local balance is only a copy, so
none of the 25 vanilla reports saw the risk.

**A code-level failure mode vanilla found more often** (K21, in-memory database; A 25 of 25, B 19). A/12, which
cites the configuration directly:

| Failure mode | Cause | Effect | S/O/D | RPN | Action |
| --- | --- | --- | --- | --- | --- |
| Persistent customer/account/payment data is lost on restart | Production configuration uses in-memory H2, `ddl-auto: create-drop`, and fixture initialisation | Accounts, balances, history, cases, and payment status disappear or revert to fixtures. Ledger/scheme reconciliation breaks; support and operations lose the audit trail | 10/3/9 | 270 | Use a supported durable production database with migrations, backups, restore drills, HA, and explicit production profiles. Fail startup if an in-memory datasource is used outside tests |

B/12 did find it, folded into a wider "service unavailable or data lost on restart" row; six B reports didn't.

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

- **Second judge** (all 75 reports, without my hand-check overrides): recall A 61%, B 76%, C 80%; B − A +15 points
  (p = 0.0001). It agreed with the primary judge on 1,597 of 1,650 found / not-found decisions (97%). Context-only
  recall A 19%, B 69%, C 73%. In-code recall A 80%, B 75%, C 78%: the same entries dropped (K21 restart data loss: A 25,
  B 19; K22 every call refused: A 20, B 13; of 25), but the in-code gap is smaller under this judge, B − A −5 points
  (two-sided p = 0.08), so the crowding-out result rests on the primary judge and should be read as a lead.
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
  the context-only entries B added took the place of in-code entries A had found. This is exploratory, and weaker
  under the second judge (−5 points, p = 0.08, against −8, p = 0.005), though the same entries drop under both.
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
- The second judge's verdicts were not hand-checked, and neither were the "extra failure modes" verdicts.
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
the second judge on a subset (credit; later completed on all 75), the hand check as done, mixed models replaced by an entry-level check, an
exploratory section added, an H5 display bug fixed, my pilot description of F6's failure corrected, and the payback
assumption.
