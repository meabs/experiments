# okf-context analysis: pilot

Feature runs: 9. FMEA reports judged: 6 (judge `google/gemini-4-argon`, hand overrides for 1 runs).

## Headline

| Arm | Feature changes fully correct (share of runs, higher is better) | FMEA recall (share of the 22 answer-key failure modes found, mean per run, higher is better) | Invented facts per FMEA (mean, lower is better) |
| --- | --- | --- | --- |
| A | 100% (6/6) | 59% (n=3) | 0.0 |
| B | 100% (3/3) | 71% (n=3) | 0.0 |
| C | n/a | n/a | n/a |

## Pre-registered hypotheses

Differences are B - A unless stated, in percentage points of the measure's 0-100% scale. p values are one-sided permutation tests (two-sided for H5); H2 to H7 are Holm-adjusted together at 0.05; H1 is an equivalence test, judged on its own 90% interval.

| # | Statement | Observed | Interval | p (raw) | Verdict |
| --- | --- | --- | --- | --- | --- |
| H1 | features: B - A within +-15 points (TOST) | +0 points | 90% CI +0 to +0 | - | equivalent within 15 points |
| H2 | FMEA recall B > A | +12 points | 95% CI +2 to +26 | 0.1452 | Holm p = 0.4356: not supported |
| H3 | OKF benefit larger for FMEA than features | +12 points | - | 0.1494 | Holm p = 0.4356: not supported |
| H4 | fewer invented facts with B | +0.00 per report (A - B) | - | 1.0000 | Holm p = 1.0000: not supported |
| H6 | B's gain larger on context-only than in-code FMEA entries | +69 points | - | 0.0488 | Holm p = 0.2440: not supported |
| H7 | B's gain larger on role than internals FMEA entries | +39 points | - | 0.0488 | Holm p = 0.2440: not supported |

## 1. Feature changes in depth

Fully correct runs per ticket (every hidden test and every existing test passed; Wilson 95% interval; higher is better).

| Ticket | Rules | A | B | C |
| --- | --- | --- | --- | --- |
| F1 | in code | 2/2 (34%-100%) | 1/1 (21%-100%) | - |
| F2 | in code | 2/2 (34%-100%) | 1/1 (21%-100%) | - |
| F3 | in code | 2/2 (34%-100%) | 1/1 (21%-100%) | - |
| F6 | integration (context only) | - | - | - |
| F7 | integration (context only) | - | - | - |

Each hidden test: runs that passed it, of runs (higher is better). `integration_` tests check a rule of an external system's behaviour; builds that failed count as failing every test.

| Ticket | Hidden test | A | B | C |
| --- | --- | --- | --- | --- |
| F1 | access_assignedSupportAndAdminSeeThem | 2/2 | 1/1 | 0/0 |
| F1 | access_othersGetNotFound | 2/2 | 1/1 | 0/0 |
| F1 | functional_onlyThatAccountsPayments | 2/2 | 1/1 | 0/0 |
| F1 | functional_ownerListsPaymentsNewestFirst | 2/2 | 1/1 | 0/0 |
| F1 | functional_statusFilter | 2/2 | 1/1 | 0/0 |
| F1 | functional_unknownStatusIsBadRequest | 2/2 | 1/1 | 0/0 |
| F2 | access_needsTheWriteScope | 2/2 | 1/1 | 0/0 |
| F2 | access_onlyTheHolderCancels | 2/2 | 1/1 | 0/0 |
| F2 | functional_cancelledPaymentIsNeverSent | 2/2 | 1/1 | 0/0 |
| F2 | functional_holderCancelsAQueuedPayment | 2/2 | 1/1 | 0/0 |
| F2 | functional_otherStatusesConflict | 2/2 | 1/1 | 0/0 |
| F3 | access_staffWhoLookAfterTheAccountSeeIt | 2/2 | 1/1 | 0/0 |
| F3 | functional_agreesWithTheLimitCheck | 2/2 | 1/1 | 0/0 |
| F3 | functional_countsTodaysPayments | 2/2 | 1/1 | 0/0 |
| F3 | functional_nothingPaidYetToday | 2/2 | 1/1 | 0/0 |
| F3 | functional_queuedPaymentsCountOnTheDayTheyAreMade | 2/2 | 1/1 | 0/0 |
| F3 | functional_rejectedPaymentsDontCount | 2/2 | 1/1 | 0/0 |
| F3 | functional_ukDayBoundary | 2/2 | 1/1 | 0/0 |

- **in-code tickets (F1-F3)**: A 100%, B 100%, C n/a; B - A +0 points, 90% interval +0 to +0 (H1's sensitivity to the ticket mix, section 6).

Runs that changed protected files (the grader restores them): F1 A/1: src/test/java/com/example/accounts/PaymentApiTest.java; F2 A/1: src/test/java/com/example/accounts/PaymentApiTest.java; F2 A/2: src/test/java/com/example/accounts/PaymentApiTest.java; F3 A/1: src/test/java/com/example/accounts/PaymentApiTest.java; F3 A/2: src/test/java/com/example/accounts/PaymentApiTest.java; F2 B/1: src/test/java/com/example/accounts/PaymentApiTest.java.

Failure taxonomy (labelled from the diff and transcript by the judge model and me; Cohen's kappa) is in `results/<stage>/taxonomy.md` once labelled.

## 2. Service FMEA in depth

Recall: share of the answer key's failure modes a report contains (mean per run; in brackets the lowest and highest run; higher is better). Lenient: the same failure mode; strict: the same mode and cause.

| Answer-key entries | A | B | C |
| --- | --- | --- | --- |
| all 22 (lenient, primary) | 59% (55%-64%) | 71% (64%-86%) | - |
| all 22 (strict) | 58% (55%-59%) | 67% (59%-82%) | - |
| 8 context-only | 25% (12%-38%) | 71% (50%-100%) | - |
| 4 inferable | 50% (50%-50%) | 83% (75%-100%) | - |
| 10 in code | 90% (90%-90%) | 67% (60%-70%) | - |
| 14 about the service's role | 50% (43%-57%) | 76% (64%-93%) | - |
| 8 about internals | 75% (75%-75%) | 62% (50%-75%) | - |
| 12 high-severity (S >= 8) | 64% (58%-67%) | 67% (58%-83%) | - |

Each answer-key entry: reports that contained it, of reports (higher is better).

| Key | Failure mode | Source | About | A | B | C |
| --- | --- | --- | --- | --- | --- | --- |
| K01 | A payment is booked twice in the core ledger | context only | role | 2/3 | 3/3 | 0/0 |
| K02 | The scheme accepts a payment but the service loses its record of it | inferable | role | 3/3 | 3/3 | 0/0 |
| K03 | Payments are sent without fraud screening | context only | role | 3/3 | 3/3 | 0/0 |
| K04 | A payment goes through unscreened when the fraud service is slow or down | context only | role | 0/3 | 1/3 | 0/0 |
| K05 | A fraud REFER is treated as a rejection | context only | role | 0/3 | 1/3 | 0/0 |
| K06 | Payments queued for a bank holiday are rejected by the scheme | inferable | role | 0/3 | 3/3 | 0/0 |
| K07 | Queued payments are not sent on their execution date | in code | role | 3/3 | 3/3 | 0/0 |
| K08 | A customer notification contains a full account number or sort code | context only | role | 0/3 | 1/3 | 0/0 |
| K09 | Customers are not told about their payments | in code | role | 3/3 | 3/3 | 0/0 |
| K10 | An account is closed with money still in it | context only | role | 0/3 | 3/3 | 0/0 |
| K11 | Payments are approved or refused against an out-of-date balance | context only | role | 1/3 | 2/3 | 0/0 |
| K12 | Statements are wrong or missing | context only | role | 0/3 | 3/3 | 0/0 |
| K13 | Payments sent to the scheme are never posted to the ledger | inferable | role | 3/3 | 3/3 | 0/0 |
| K14 | A customer's payment is created twice | in code | internals | 3/3 | 1/3 | 0/0 |
| K15 | The daily limit is exceeded | in code | internals | 3/3 | 3/3 | 0/0 |
| K16 | An account is overdrawn by payments | in code | internals | 3/3 | 3/3 | 0/0 |
| K17 | Payments around the cut-off are sent or queued wrongly | inferable | internals | 0/3 | 1/3 | 0/0 |
| K18 | The customer isn't told that the scheme rejected their payment | in code | internals | 0/3 | 1/3 | 0/0 |
| K19 | One bank's data is visible to another (tenant isolation fails) | in code | internals | 3/3 | 3/3 | 0/0 |
| K20 | Someone other than the account holder makes a payment | in code | internals | 3/3 | 0/3 | 0/0 |
| K21 | Data is lost when the service restarts | in code | internals | 3/3 | 3/3 | 0/0 |
| K22 | Nobody can use the app or back office: every call is refused | in code | role | 3/3 | 0/3 | 0/0 |

Quality of the matched entries (share of matched entries meeting each criterion; higher is better).

| Criterion | A | B | C |
| --- | --- | --- | --- |
| effect on customers right | 100% | 100% | - |
| cause plausible for this code | 100% | 98% | - |
| detection method concrete | 100% | 98% | - |
| action addresses the cause | 100% | 96% | - |
| dependants named (share of the key's dependants for the entry) | 84% | 90% | - |

Scoring sense: Spearman rank correlation between a report's risk priority numbers and the key's, over its matched entries (mean per report; 1 = same order; higher is better): A 0.32 (n=3), B 0.27 (n=3).

Invented facts by class (total over reports; per 1,000 words in brackets; lower is better).

| Class | A | B | C |
| --- | --- | --- | --- |
| external_system | 0 (0.00) | 0 (0.00) | 0 (0.00) |
| rule_or_number | 0 (0.00) | 0 (0.00) | 0 (0.00) |
| code_claim | 0 (0.00) | 0 (0.00) | 0 (0.00) |
| contradicts_context | 0 (0.00) | 0 (0.00) | 0 (0.00) |

Extra failure modes not in the key (mean per report): A: valid 3.0, generic 1.7, wrong 0.0; B: valid 1.7, generic 0.0, wrong 0.7. Valid extras are listed in `extras-valid.md` and reported as gaps in the key, not added to it.

*Exploratory.* Dependants mentioned at all (of 9, mean per report; higher is better): A 7.3, B 9.0.

Structure: words per report A 2096, B 1998; rows per report A 15.3, B 15.3.

## 3. How the agent used the context

Traceability: reports containing each distinctive fact of the system context (count of reports). A fact in an A report came from the code, from general knowledge, or was a guess.

| Fact | A | B | C |
| --- | --- | --- | --- |
| four hours | 0/3 | 0/3 | - |
| 2 seconds (screening) | 1/3 | 1/3 | - |
| FRD-7 | 0/3 | 3/3 | - |
| fails closed | 2/3 | 2/3 | - |
| 02:00 balance copy | 0/3 | 2/3 | - |
| 07:00 reconciliation | 0/3 | 3/3 | - |
| 5th working day | 0/3 | 3/3 | - |
| 8 weeks (complaints) | 0/3 | 0/3 | - |
| DT01 | 0/3 | 3/3 | - |
| DUPL | 0/3 | 0/3 | - |
| 24 hours (ledger) | 0/3 | 0/3 | - |
| 30 days (scheme) | 0/3 | 1/3 | - |
| idempotency | 3/3 | 3/3 | - |

Exploration per run (means). Codex puts AGENTS.md into the prompt itself, so C always has its section; for B, "read okf" is whether the run opened the bundle.

| Task | Arm | Runs | Read okf | Commands | Source files opened | Commands before the first edit | Seconds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| F1 | A | 2 | - | 8 | 16 | 4 | 90 |
| F1 | B | 1 | 1/1 | 9 | 13 | 4 | 79 |
| F2 | A | 2 | - | 8 | 13 | 5 | 89 |
| F2 | B | 1 | 1/1 | 7 | 11 | 5 | 90 |
| F3 | A | 2 | - | 10 | 17 | 6 | 92 |
| F3 | B | 1 | 1/1 | 7 | 19 | 5 | 72 |
| FMEA | A | 3 | - | 13 | 17 | 11 | 118 |
| FMEA | B | 3 | 3/3 | 8 | 8 | 5 | 120 |

Bundle files opened by B runs (count of runs): (listing or search) 8, architecture 8, context 8, index 8, system 7.

*Exploratory (correlation only).* B FMEA recall when the run opened the bundle: 71% (n=3); when it didn't: n/a (n=0).

## 5. Consistency and cost

| Ticket | A | B | C |
| --- | --- | --- | --- |
| F1 | all agree (2/2) | all agree (1/1) | - |
| F2 | all agree (2/2) | all agree (1/1) | - |
| F3 | all agree (2/2) | all agree (1/1) | - |
| F6 | - | - | - |
| F7 | - | - | - |

FMEA recall spread (standard deviation over reports, points; lower is steadier): A 3.7, B 10.7.
Entries found only sometimes (20-80% of reports): K01 in A (2/3), K04 in B (1/3), K05 in B (1/3), K08 in B (1/3), K11 in A (1/3), K11 in B (2/3), K14 in B (1/3), K17 in B (1/3), K18 in B (1/3).

Cost per run at list price (lower is better). Last column: cost per correct result (per fully correct feature change; per answer-key entry found).

| Task | Arm | Runs | Input tokens | Output tokens | Seconds | Cost per run | Cost per correct result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| features | A | 6 | 316k | 3.8k | 90 | $0.123 | $0.123 |
| features | B | 3 | 279k | 3.4k | 80 | $0.109 | $0.109 |
| FMEA | A | 3 | 247k | 5.7k | 118 | $0.140 | $0.011 |
| FMEA | B | 3 | 337k | 5.5k | 120 | $0.150 | $0.010 |
