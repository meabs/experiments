# okf-context analysis: main

Feature runs: 75. FMEA reports judged: 75 (judge `google/gemini-4-argon`, hand overrides for 31 runs).

## Headline

| Arm | Feature changes fully correct (share of runs, higher is better) | FMEA recall (share of the 22 answer-key failure modes found, mean per run, higher is better) | Invented facts per FMEA (mean, lower is better) |
| --- | --- | --- | --- |
| A | 64% (16/25) | 62% (n=25) | 0.2 |
| B | 100% (25/25) | 77% (n=25) | 0.0 |
| C | 92% (23/25) | 81% (n=25) | 0.1 |

## Pre-registered hypotheses

Differences are B - A unless stated, in percentage points of the measure's 0-100% scale. p values are one-sided permutation tests (two-sided for H5); H2 to H7 are Holm-adjusted together at 0.05; H1 is an equivalence test, judged on its own 90% interval.

| # | Statement | Observed | Interval | p (raw) | Verdict |
| --- | --- | --- | --- | --- | --- |
| H1 | features: B - A within +-15 points (TOST) | +36 points | 90% CI +0 to +72 | - | inconclusive |
| H2 | FMEA recall B > A | +15 points | 95% CI +11 to +19 | 0.0001 | Holm p = 0.0007: supported |
| H3 | OKF benefit larger for FMEA than features | -21 points | - | 0.9695 | Holm p = 0.9819: not supported |
| H4 | fewer invented facts with B | +0.16 per report (A - B) | - | 0.0552 | Holm p = 0.2208: not supported |
| H5 (features) | B and C differ | -8 points (C - B) | - | 0.4910 | Holm p = 0.9819: not supported |
| H5 (FMEA) | B and C differ | +4 points (C - B) | - | 0.1011 | Holm p = 0.3033: not supported |
| H6 | B's gain larger on context-only than in-code FMEA entries | +61 points | - | 0.0001 | Holm p = 0.0007: supported |
| H7 | B's gain larger on role than internals FMEA entries | +34 points | - | 0.0001 | Holm p = 0.0007: supported |

## 1. Feature changes in depth

Fully correct runs per ticket (every hidden test and every existing test passed; Wilson 95% interval; higher is better).

| Ticket | Rules | A | B | C |
| --- | --- | --- | --- | --- |
| F1 | in code | 5/5 (57%-100%) | 5/5 (57%-100%) | 5/5 (57%-100%) |
| F2 | in code | 5/5 (57%-100%) | 5/5 (57%-100%) | 5/5 (57%-100%) |
| F3 | in code | 5/5 (57%-100%) | 5/5 (57%-100%) | 5/5 (57%-100%) |
| F6 | integration (context only) | 1/5 (4%-62%) | 5/5 (57%-100%) | 3/5 (23%-88%) |
| F7 | integration (context only) | 0/5 (0%-43%) | 5/5 (57%-100%) | 5/5 (57%-100%) |

Each hidden test: runs that passed it, of runs (higher is better). `integration_` tests check a rule of an external system's behaviour; builds that failed count as failing every test.

| Ticket | Hidden test | A | B | C |
| --- | --- | --- | --- | --- |
| F1 | access_assignedSupportAndAdminSeeThem | 5/5 | 5/5 | 5/5 |
| F1 | access_othersGetNotFound | 5/5 | 5/5 | 5/5 |
| F1 | functional_onlyThatAccountsPayments | 5/5 | 5/5 | 5/5 |
| F1 | functional_ownerListsPaymentsNewestFirst | 5/5 | 5/5 | 5/5 |
| F1 | functional_statusFilter | 5/5 | 5/5 | 5/5 |
| F1 | functional_unknownStatusIsBadRequest | 5/5 | 5/5 | 5/5 |
| F2 | access_needsTheWriteScope | 5/5 | 5/5 | 5/5 |
| F2 | access_onlyTheHolderCancels | 5/5 | 5/5 | 5/5 |
| F2 | functional_cancelledPaymentIsNeverSent | 5/5 | 5/5 | 5/5 |
| F2 | functional_holderCancelsAQueuedPayment | 5/5 | 5/5 | 5/5 |
| F2 | functional_otherStatusesConflict | 5/5 | 5/5 | 5/5 |
| F3 | access_staffWhoLookAfterTheAccountSeeIt | 5/5 | 5/5 | 5/5 |
| F3 | functional_agreesWithTheLimitCheck | 5/5 | 5/5 | 5/5 |
| F3 | functional_countsTodaysPayments | 5/5 | 5/5 | 5/5 |
| F3 | functional_nothingPaidYetToday | 5/5 | 5/5 | 5/5 |
| F3 | functional_queuedPaymentsCountOnTheDayTheyAreMade | 5/5 | 5/5 | 5/5 |
| F3 | functional_rejectedPaymentsDontCount | 5/5 | 5/5 | 5/5 |
| F3 | functional_ukDayBoundary | 5/5 | 5/5 | 5/5 |
| F6 | functional_resubmitCompletesThePayment | 5/5 | 5/5 | 5/5 |
| F6 | functional_timeoutKeepsThePayment | 5/5 | 5/5 | 5/5 |
| F6 | integration_acceptedBeforeTheTimeoutIsNotPaidTwice | 1/5 | 5/5 | 3/5 |
| F6 | integration_resubmitUsesTheSameReference | 5/5 | 5/5 | 5/5 |
| F7 | functional_notificationFailureDoesNotFailThePayment | 5/5 | 5/5 | 5/5 |
| F7 | functional_queuedPaymentIsNotified | 5/5 | 5/5 | 5/5 |
| F7 | functional_rejectedPaymentIsNotified | 5/5 | 5/5 | 5/5 |
| F7 | functional_sentPaymentStillGetsOneMessage | 5/5 | 5/5 | 5/5 |
| F7 | integration_neverTheFullAccountNumber | 5/5 | 5/5 | 5/5 |
| F7 | integration_queuedUsesTheServicesTemplate | 5/5 | 5/5 | 5/5 |
| F7 | integration_rejectedUsesTheServicesTemplate | 0/5 | 5/5 | 5/5 |

- **in-code tickets (F1-F3)**: A 100%, B 100%, C 100%; B - A +0 points, 90% interval +0 to +0 (H1's sensitivity to the ticket mix, section 6).
- **integration tickets (F6-F7)**: A 10%, B 100%, C 80%; B - A +90 points, 90% interval +70 to +100 (H1's sensitivity to the ticket mix, section 6).

Integration rule right (all `integration_` tests passed, F6 and F7; higher is better): A 1/10, B 10/10, C 8/10.

Runs that changed protected files (the grader restores them): F2 A/5: src/test/java/com/example/accounts/PaymentApiTest.java; F3 A/1: src/test/java/com/example/accounts/PaymentApiTest.java; F3 A/3: src/test/java/com/example/accounts/PaymentApiTest.java; F3 A/5: src/test/java/com/example/accounts/AccountApiTest.java, src/test/java/com/example/accounts/PaymentApiTest.java; F7 A/3: src/test/java/com/example/accounts/PaymentApiTest.java; F1 B/4: src/test/java/com/example/accounts/PaymentApiTest.java; F2 B/3: src/test/java/com/example/accounts/PaymentApiTest.java; F2 B/4: src/test/java/com/example/accounts/PaymentApiTest.java; F2 B/5: src/test/java/com/example/accounts/PaymentApiTest.java; F3 B/1: src/test/java/com/example/accounts/PaymentApiTest.java; F3 B/3: src/test/java/com/example/accounts/PaymentApiTest.java; F3 B/4: src/test/java/com/example/accounts/PaymentApiTest.java; F3 B/5: src/test/java/com/example/accounts/PaymentApiTest.java; F6 B/2: src/test/java/com/example/accounts/PaymentApiTest.java; F6 B/3: src/test/java/com/example/accounts/PaymentApiTest.java; F6 B/4: src/test/java/com/example/accounts/PaymentApiTest.java; F7 B/1: src/test/java/com/example/accounts/PaymentApiTest.java; F7 B/2: src/test/java/com/example/accounts/PaymentApiTest.java; F7 B/3: src/test/java/com/example/accounts/PaymentApiTest.java; F7 B/5: src/test/java/com/example/accounts/PaymentApiTest.java; F1 C/2: src/test/java/com/example/accounts/PaymentApiTest.java; F1 C/3: src/test/java/com/example/accounts/PaymentApiTest.java; F1 C/4: src/test/java/com/example/accounts/PaymentApiTest.java; F2 C/1: src/test/java/com/example/accounts/PaymentApiTest.java; F2 C/2: src/test/java/com/example/accounts/PaymentApiTest.java; F3 C/5: src/test/java/com/example/accounts/PaymentApiTest.java; F6 C/1: src/test/java/com/example/accounts/PaymentApiTest.java; F6 C/5: src/test/java/com/example/accounts/PaymentApiTest.java.

Failure taxonomy (labelled from the diff and transcript by the judge model and me; Cohen's kappa) is in `results/<stage>/taxonomy.md` once labelled.

## 2. Service FMEA in depth

Recall: share of the answer key's failure modes a report contains (mean per run; in brackets the lowest and highest run; higher is better). Lenient: the same failure mode; strict: the same mode and cause.

| Answer-key entries | A | B | C |
| --- | --- | --- | --- |
| all 22 (lenient, primary) | 62% (50%-77%) | 77% (64%-91%) | 81% (64%-95%) |
| all 22 (strict) | 56% (45%-68%) | 73% (55%-91%) | 77% (64%-91%) |
| 7 context-only | 17% (0%-43%) | 70% (43%-100%) | 72% (43%-100%) |
| 5 inferable | 83% (60%-100%) | 92% (80%-100%) | 97% (80%-100%) |
| 10 in code | 82% (70%-90%) | 74% (50%-90%) | 78% (60%-100%) |
| 14 about the service's role | 54% (43%-71%) | 81% (64%-100%) | 81% (64%-100%) |
| 8 about internals | 76% (62%-88%) | 70% (50%-88%) | 80% (50%-100%) |
| 12 high-severity (S >= 8) | 59% (42%-75%) | 77% (50%-100%) | 79% (58%-100%) |

Each answer-key entry: reports that contained it, of reports (higher is better).

| Key | Failure mode | Source | About | A | B | C |
| --- | --- | --- | --- | --- | --- | --- |
| K01 | A payment is booked twice in the core ledger | context only | role | 15/25 | 25/25 | 25/25 |
| K02 | The scheme accepts a payment but the service loses its record of it | inferable | role | 24/25 | 25/25 | 25/25 |
| K03 | Payments are sent without fraud screening | inferable | role | 25/25 | 25/25 | 25/25 |
| K04 | A payment goes through unscreened when the fraud service is slow or down | context only | role | 4/25 | 6/25 | 12/25 |
| K05 | A fraud REFER is treated as a rejection | context only | role | 0/25 | 5/25 | 8/25 |
| K06 | Payments queued for a bank holiday are rejected by the scheme | inferable | role | 14/25 | 25/25 | 25/25 |
| K07 | Queued payments are not sent on their execution date | in code | role | 25/25 | 24/25 | 25/25 |
| K08 | A customer notification contains a full account number or sort code | context only | role | 0/25 | 13/25 | 9/25 |
| K09 | Customers are not told about their payments | in code | role | 25/25 | 25/25 | 22/25 |
| K10 | An account is closed with money still in it | context only | role | 0/25 | 25/25 | 25/25 |
| K11 | Payments are approved or refused against an out-of-date balance | context only | role | 8/25 | 25/25 | 24/25 |
| K12 | Statements are wrong or missing | context only | role | 3/25 | 23/25 | 23/25 |
| K13 | Payments sent to the scheme are never posted to the ledger | inferable | role | 25/25 | 25/25 | 25/25 |
| K14 | A customer's payment is created twice | in code | internals | 21/25 | 18/25 | 20/25 |
| K15 | The daily limit is exceeded | in code | internals | 25/25 | 24/25 | 25/25 |
| K16 | An account is overdrawn by payments | in code | internals | 25/25 | 24/25 | 25/25 |
| K17 | Payments around the cut-off are sent or queued wrongly | inferable | internals | 16/25 | 15/25 | 21/25 |
| K18 | The customer isn't told that the scheme rejected their payment | in code | internals | 0/25 | 0/25 | 5/25 |
| K19 | One bank's data is visible to another (tenant isolation fails) | in code | internals | 25/25 | 25/25 | 25/25 |
| K20 | Someone other than the account holder makes a payment | in code | internals | 15/25 | 14/25 | 18/25 |
| K21 | Data is lost when the service restarts | in code | internals | 25/25 | 19/25 | 20/25 |
| K22 | Nobody can use the app or back office: every call is refused | in code | role | 20/25 | 13/25 | 11/25 |

Quality of the matched entries (share of matched entries meeting each criterion; higher is better).

| Criterion | A | B | C |
| --- | --- | --- | --- |
| effect on customers right | 96% | 98% | 99% |
| cause plausible for this code | 99% | 100% | 100% |
| detection method concrete | 97% | 94% | 94% |
| action addresses the cause | 99% | 99% | 99% |
| dependants named (share of the key's dependants for the entry) | 76% | 86% | 84% |

Scoring sense: Spearman rank correlation between a report's risk priority numbers and the key's, over its matched entries (mean per report; 1 = same order; higher is better): A 0.39 (n=25), B 0.50 (n=25), C 0.58 (n=25).

Invented facts by class (total over reports; per 1,000 words in brackets; lower is better).

| Class | A | B | C |
| --- | --- | --- | --- |
| external_system | 0 (0.00) | 0 (0.00) | 0 (0.00) |
| rule_or_number | 0 (0.00) | 0 (0.00) | 0 (0.00) |
| code_claim | 2 (0.04) | 0 (0.00) | 2 (0.03) |
| contradicts_context | 2 (0.04) | 0 (0.00) | 0 (0.00) |

Extra failure modes not in the key (mean per report): A: valid 3.2, generic 1.8, wrong 0.4; B: valid 1.5, generic 0.6, wrong 0.1; C: valid 2.7, generic 0.8, wrong 0.2. Valid extras are listed in `extras-valid.md` and reported as gaps in the key, not added to it.

*Exploratory.* Dependants mentioned at all (of 9, mean per report; higher is better): A 7.5, B 8.9, C 8.6.

Structure: words per report A 2204, B 2168, C 2413; rows per report A 15.9, B 15.6, C 18.4.

## 3. How the agent used the context

Traceability: reports containing each distinctive fact of the system context (count of reports). A fact in an A report came from the code, from general knowledge, or was a guess.

| Fact | A | B | C |
| --- | --- | --- | --- |
| four hours | 0/25 | 7/25 | 3/25 |
| 2 seconds (screening) | 5/25 | 1/25 | 5/25 |
| FRD-7 | 0/25 | 23/25 | 23/25 |
| fails closed | 18/25 | 19/25 | 17/25 |
| 02:00 balance copy | 0/25 | 25/25 | 17/25 |
| 07:00 reconciliation | 0/25 | 23/25 | 13/25 |
| 5th working day | 0/25 | 22/25 | 17/25 |
| 8 weeks (complaints) | 0/25 | 2/25 | 0/25 |
| DT01 | 0/25 | 25/25 | 25/25 |
| DUPL | 1/25 | 0/25 | 4/25 |
| 24 hours (ledger) | 0/25 | 2/25 | 0/25 |
| 30 days (scheme) | 0/25 | 2/25 | 0/25 |
| idempotency | 25/25 | 25/25 | 25/25 |

Exploration per run (means). Codex puts AGENTS.md into the prompt itself, so C always has its section; for B, "read okf" is whether the run opened the bundle.

| Task | Arm | Runs | Read okf | Commands | Source files opened | Commands before the first edit | Seconds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| F1 | A | 5 | - | 6 | 14 | 4 | 68 |
| F1 | B | 5 | 5/5 | 8 | 12 | 5 | 82 |
| F1 | C | 5 | - | 7 | 14 | 4 | 73 |
| F2 | A | 5 | - | 10 | 16 | 8 | 70 |
| F2 | B | 5 | 5/5 | 7 | 13 | 4 | 76 |
| F2 | C | 5 | - | 6 | 13 | 4 | 64 |
| F3 | A | 5 | - | 7 | 15 | 4 | 77 |
| F3 | B | 5 | 5/5 | 9 | 15 | 6 | 101 |
| F3 | C | 5 | - | 8 | 15 | 5 | 73 |
| F6 | A | 5 | - | 6 | 13 | 3 | 78 |
| F6 | B | 5 | 5/5 | 10 | 11 | 5 | 108 |
| F6 | C | 5 | - | 7 | 13 | 4 | 88 |
| F7 | A | 5 | - | 8 | 10 | 5 | 79 |
| F7 | B | 5 | 5/5 | 12 | 11 | 9 | 88 |
| F7 | C | 5 | - | 7 | 9 | 4 | 70 |
| FMEA | A | 25 | - | 10 | 15 | 8 | 121 |
| FMEA | B | 25 | 25/25 | 11 | 14 | 10 | 119 |
| FMEA | C | 25 | - | 14 | 17 | 12 | 126 |

Bundle files opened by B runs (count of runs): architecture 50, context 50, index 50, (listing or search) 48, system 48.

*Exploratory (correlation only).* B FMEA recall when the run opened the bundle: 77% (n=25); when it didn't: n/a (n=0).

## 5. Consistency and cost

| Ticket | A | B | C |
| --- | --- | --- | --- |
| F1 | all agree (5/5) | all agree (5/5) | all agree (5/5) |
| F2 | all agree (5/5) | all agree (5/5) | all agree (5/5) |
| F3 | all agree (5/5) | all agree (5/5) | all agree (5/5) |
| F6 | mixed (1/5) | all agree (5/5) | mixed (3/5) |
| F7 | all agree (0/5) | all agree (5/5) | all agree (5/5) |

FMEA recall spread (standard deviation over reports, points; lower is steadier): A 6.6, B 7.1, C 7.0.
Entries found only sometimes (20-80% of reports): K01 in A (15/25), K04 in B (6/25), K04 in C (12/25), K05 in B (5/25), K05 in C (8/25), K06 in A (14/25), K08 in B (13/25), K08 in C (9/25), K11 in A (8/25), K14 in B (18/25), K14 in C (20/25), K17 in A (16/25), K17 in B (15/25), K18 in C (5/25), K20 in A (15/25), K20 in B (14/25), K20 in C (18/25), K21 in B (19/25), K21 in C (20/25), K22 in A (20/25), K22 in B (13/25), K22 in C (11/25).

Cost per run at list price (lower is better). Last column: cost per correct result (per fully correct feature change; per answer-key entry found).

| Task | Arm | Runs | Input tokens | Output tokens | Seconds | Cost per run | Cost per correct result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| features | A | 25 | 232k | 3.2k | 74 | $0.014 | $0.022 |
| features | B | 25 | 352k | 3.8k | 91 | $0.018 | $0.018 |
| features | C | 25 | 263k | 3.1k | 74 | $0.015 | $0.016 |
| FMEA | A | 25 | 329k | 5.8k | 121 | $0.022 | $1.64 per 1,000 |
| FMEA | B | 25 | 300k | 5.6k | 119 | $0.021 | $1.24 per 1,000 |
| FMEA | C | 25 | 308k | 6.0k | 126 | $0.021 | $1.21 per 1,000 |

## 6a. Exploratory checks (not pre-registered as hypotheses; not Holm-adjusted)

Recall differences between arms, two-sided permutation over reports (points; 95% bootstrap interval).

| Entries | Difference | Points | 95% CI | p (two-sided) |
| --- | --- | --- | --- | --- |
| 10 in-code entries | B - A | -8 | -13 to -3 | 0.0048 |
| 10 in-code entries | C - A | -4 | -9 to +1 | 0.1570 |
| 10 in-code entries | C - B | +4 | -2 to +10 | 0.2466 |
| 8 internals entries | B - A | -7 | -13 to +0 | 0.0763 |
| 8 internals entries | C - A | +4 | -3 to +9 | 0.3418 |
| 8 internals entries | C - B | +10 | +3 to +17 | 0.0112 |
| 7 context-only entries | B - A | +53 | +45 to +61 | 0.0001 |
| 7 context-only entries | C - A | +55 | +47 to +63 | 0.0001 |
| 7 context-only entries | C - B | +2 | -6 to +11 | 0.7005 |
| all 22 entries | B - A | +15 | +11 to +19 | 0.0001 |
| all 22 entries | C - A | +19 | +15 to +22 | 0.0001 |
| all 22 entries | C - B | +4 | -0 to +7 | 0.1011 |

Entry-level check: each answer-key entry is the unit (its share of reports that found it), resampled over entries. Replaces the planned mixed model; see the amendment log.

| Entries | Difference | Mean points | 95% CI (entries resampled) | Entries |
| --- | --- | --- | --- | --- |
| all 22 | B - A | +15 | +2 to +30 | 9 up, 8 down, 5 level |
| all 22 | C - A | +19 | +6 to +33 | 12 up, 4 down, 6 level |
| context only | B - A | +53 | +30 to +75 | 7 up, 0 down, 0 level |
| context only | C - A | +55 | +38 to +74 | 7 up, 0 down, 0 level |
| in code | B - A | -8 | -14 to -3 | 0 up, 7 down, 3 level |
| in code | C - A | -4 | -14 to +5 | 2 up, 4 down, 4 level |

## 6. Robustness

Second judge `anthropic/claude-sonnet-5.5`: FMEA recall A 61%, B 76%, C 80%; B - A +15 points, one-sided permutation p = 0.0001. Agreement with the primary judge on found / not found: 1597/1650 entry decisions (97%).
