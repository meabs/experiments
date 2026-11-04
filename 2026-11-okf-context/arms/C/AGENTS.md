# accounts-service

- Build and run the tests with `mvn -o -q test` (offline: every dependency is already in the local Maven repository).
  Do not run `mvn install`.
- README.md describes the packages, the security model and the API conventions.

## System knowledge

The key facts and pitfalls of this service, its external systems and how they behave, and the business processes it supports.

### System information

#### What it is

`accounts-service` is the bank's system of record for the customer's view of their current and savings accounts:
balances, transactions, statements, notes, support cases, closures, and **payments out**. Customers use it through
the mobile app and online banking, staff through the back office. It is multi-tenant (each tenant is a bank brand:
`acme`, `globex`). Owner: the Accounts squad. Service level: available 07:00 to 23:00 every day, target 99.9%.

It does **not** hold the money: the core ledger does. See architecture and
system context.

#### Build, run, test

- Spring Boot 3.5, Java 21, Maven, H2 in memory with fixtures in `src/main/resources/data.sql`.
- `mvn -o -q test` runs everything offline.
- Tests are API tests over MockMvc with real signed tokens; `ApiTest` is the base class. The four external systems are
  fakes in tests (`TestIntegrations`): `FakeScheme`, `FakeFraudScreening` (answers `ACCEPT` unless told otherwise;
  `unavailable()` simulates a timeout), `FakeLedger` (books each reference once, like the real ledger;
  `timeOutNext(n, applied)` simulates timeouts before or after booking) and `FakeNotifications`.
- The clock is a bean (`ClockConfig`, UK time). Tests use `MutableClock`, which starts on **Tuesday 6 October 2026,
  10:00 UK time**; payments in `data.sql` are dated relative to that.

#### Key pitfalls

1. **The balance here is a copy.** The ledger overwrites `accounts.balance` every night at 02:00; during the day the
   service debits its own copy. Anything that must be exact (closing an account at zero balance) has to be checked
   against the ledger, not the copy.
2. **The ledger `reference` is an idempotency key.** The ledger books a reference once (a repeat within 24 hours
   returns the first booking). A ledger **timeout doesn't mean the posting failed**: it may have been booked. Any retry
   must reuse the payment's original `ledgerReference`; a new reference debits the customer twice.
3. **Every payment out must be fraud-screened** before it is sent (bank policy FRD-7, since 1 November 2026). The
   client exists in `integration/fraud`; payments don't call it yet. `REFER` means **hold for review**
   (`HELD_FOR_REVIEW`), not reject. Screening **fails closed**: no answer within 2 seconds, or an error, means hold,
   never send unscreened.
4. **Never refuse a payment because of the time.** After the scheme's 15:30 cut-off, at weekends and on bank holidays,
   payments are queued (`QUEUED`) for the next working day. `WorkingDays` doesn't know bank holidays yet (known gap: the
   scheme rejects such payments with `DT01`).
5. **A scheme timeout doesn't mean the scheme refused.** It may have accepted the instruction. The scheme reference
   (`P` + payment id) is unique for 30 days, so resending the same reference is safe and a new one pays twice. Today a
   scheme timeout is not handled: the request fails and the transaction rolls back, losing the local record of a
   payment the scheme may have taken.
6. **Notifications never contain a full account number or sort code**: last four digits only (`accountEnding`).
   Notifications are best effort: a failure must never fail or undo a payment.
7. **Times are UK time.** Use the injected `Clock`, never `now()` without it, or tests and the cut-off break.
8. **Access rules** (README): 404 for anything the caller may not see, 403 for not allowed, 409 for the wrong state.
   Only the account holder can pay from an account. Never cross tenants.

### Architecture

#### Components

| Package | What it does |
| --- | --- |
| `account`, `customer`, `cases`, `closure` | accounts, customers, support cases, closure requests (`AccountService.getVisible` applies the access rules) |
| `payment` | payments out: `PaymentService` (checks, cut-off, queueing), `PaymentDispatcher` (scheme, ledger, notification), `QueuedPaymentJob` (06:00 on working days) |
| `integration/scheme` | payment scheme gateway client |
| `integration/fraud` | fraud screening client (not yet called by payments) |
| `integration/ledger` | core ledger client |
| `integration/notify` | customer notification client |
| `security`, `web`, `config` | tokens and access rules, error mapping, the UK clock |

```
 mobile app / online banking / back office
                 |
                 v
        +------------------+      screen (2 s)     +-------------------+
        | accounts-service | --------------------> | fraud screening   |
        |  PaymentService  |                       +-------------------+
        |  Dispatcher      |      submit (10 s)    +-------------------+
        |                  | --------------------> | payment scheme    |
        |                  |                       +-------------------+
        |                  |      post (5 s)       +-------------------+
        |                  | --------------------> | core ledger       | -- 02:00 balances --> accounts.balance
        |                  |                       +-------------------+
        |                  |      send             +-------------------+
        |                  | --------------------> | notifications     |
        +------------------+                       +-------------------+
```

#### The payment flow

1. `POST /api/accounts/{id}/payments` (holder only, `accounts:write`). Checks: account visible and owned, open,
   amount within the balance copy and the daily limit.
2. **Should** be screened by the fraud service here (FRD-7); not wired yet. See the fraud section for what each answer
   means.
3. On a working day before 15:30: `PaymentDispatcher.dispatch`: submit to the scheme (reference `P` + id), take the
   amount off the balance copy, post to the ledger with a new `ledgerReference`, then notify the customer.
   Otherwise: `QUEUED` with the next working day as `executionDate`; `QueuedPaymentJob.runDue()` dispatches it then.
4. Statuses: `RECEIVED`, `QUEUED`, `SUBMITTED`, `COMPLETED`, `POSTING_FAILED` (sent, ledger posting failed),
   `HELD_FOR_REVIEW` (fraud hold), `REJECTED` (scheme or fraud refused; `reasonCode`), `CANCELLED`.

#### External systems

##### Payment scheme gateway

- Settles an accepted instruction within about two hours.
- **Cut-off 15:30 UK** for same-day instructions; later ones are rejected with `DT01`, so the service queues them.
  Weekends and bank holidays likewise; bank holidays are not handled yet.
- **Reference unique for 30 days** (`DUPL` on a repeat). Resending the same reference is safe; a new reference pays
  twice.
- Reason codes: `AC01` wrong account number, `AC04` payee account closed, `DT01` invalid date, `DUPL` duplicate,
  `RR04` regulatory (sanctions).
- **Timeout 10 s.** A timeout may mean accepted. The status query `GET /v2/instructions/{reference}` tells you; the
  service doesn't use it yet, and doesn't catch the timeout (the request fails and rolls back).

##### Fraud screening

- Answers `ACCEPT`, `REFER` or `REJECT`.
- `ACCEPT`: carry on. `REFER`: **hold**: status `HELD_FOR_REVIEW`, not sent, balance not touched, customer told it is
  being checked (`PAYMENT_UNDER_REVIEW`); the fraud team reviews within four hours (08:00 to 20:00) in its own tool.
  `REJECT`: status `REJECTED`, reason code `FRAUD`, not sent; the customer is never told why.
- **Fails closed:** no answer within **2 seconds** (`FraudScreeningUnavailableException`), or an error, is treated as
  `REFER`. Never send an unscreened payment.

##### Core ledger

- System of record for money; finance's books come from it.
- `reference` is the **idempotency key**: booked once; a repeat within 24 hours returns the first booking.
- **Timeout 5 s** (`LedgerTimeoutException`). A timeout may mean booked. The dispatcher marks the payment
  `POSTING_FAILED`; operations repost from the daily exceptions report, with the same reference. **Any automatic retry
  must reuse `ledgerReference`.**
- At 02:00 the ledger sends every balance, overwriting `accounts.balance`.

##### Customer notifications

- Templates: `PAYMENT_SENT`, `PAYMENT_QUEUED`, `PAYMENT_UNDER_REVIEW`, `PAYMENT_FAILED`.
- **Last four digits only** (`accountEnding`), never a full account number or sort code: a full number is a reportable
  data-protection breach.
- **Best effort:** catch and log failures; never fail or undo a payment for one; no retries.

### System context

#### What the accounts service does

It is the bank's system of record for the **customer's view** of their accounts: balances, transactions, monthly
statements, account notes, support cases, closures and payments out. Customers reach it through the mobile app and
online banking; staff through the back office. It sits between those channels and core banking: it does not hold the
money, which lives in the core ledger, and it sends payments through the payment scheme after the fraud service has
screened them.

#### Business processes

##### Paying someone (a bill, rent, a friend)

The customer enters the payee and amount in the app. The service checks the account, the balance and the daily
limit, asks the fraud service to screen the payment (`ACCEPT`, `REFER` or `REJECT`), sends accepted payments to the
payment scheme and posts them to the core ledger, and tells the customer. `REFER` means the payment is held for the
fraud team to review within **four hours**; it is not a rejection. Payments after the scheme's **15:30** cut-off, at
weekends or on bank holidays are queued for the next working day and sent by the 06:00 job; the time of day never
refuses a payment.

##### Statements and the regulatory return

Statements are cut on the 1st of each month from the ledger's closing balances. Regulatory reporting builds the
monthly return to the regulator from them by the **5th working day**. A wrong or missing statement makes the return
wrong.

##### Closing an account

The holder or an admin asks; an approver decides. An account may only be closed at a zero balance, **checked against
the ledger**; closing with money left in it strands the customer's funds until operations remediate by hand.

##### Complaints

The complaints team reads account notes, cases and payment history; the regulator gives the bank **8 weeks** to
answer a complaint. Records must be complete and never silently changed.

#### Who depends on it

| Dependant | What they need |
| --- | --- |
| Customers (app, online banking) | right balances and statuses; payments sent when promised; never paid twice |
| Back-office staff | accounts, notes, cases, closure approvals |
| Finance reconciliation | at **07:00** every morning it matches ledger postings to the scheme's settlement report by payment reference; a double posting, or a payment sent but not posted, is a break a person must investigate |
| Fraud team | held payments, with the screening result, to review within four hours |
| Regulatory reporting | complete, correct statements for the monthly return |
| Complaints team | complete notes and payment history |
| Operations | the daily exceptions report: `POSTING_FAILED` payments, and `QUEUED` payments past their date |

#### Rules that come from outside the code

1. Every payment out is screened (policy FRD-7). Screening **fails closed**: no answer within 2 seconds means hold,
   never send.
2. `REFER` is a hold for review, not a rejection. `REJECT` gets reason code `FRAUD`; the customer is never told why.
3. Ledger postings are idempotent on their reference for 24 hours. A timed-out posting may have been booked; a retry
   reuses the reference, or the customer is debited twice and reconciliation breaks.
4. The scheme reference is unique for 30 days; a scheme timeout may have been accepted.
5. Notifications never contain a full account number (last four digits only) and are best effort.
6. The balance in this service is a copy, overwritten from the ledger at 02:00.
