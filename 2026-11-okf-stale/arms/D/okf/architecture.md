---
type: guide
title: Architecture
description: Components of accounts-service, the payment flow, and the rules and failure behaviour of each external system.
status: stable
generated:
  by: human:accounts-squad
  at: "2026-02-27T16:00:00+00:00"
verified:
  by: human:accounts-squad
  at: "2026-03-03T10:00:00+00:00"
stale_after: "2026-06-01T00:00:00+00:00"
sources:
  - resource: /context.md
  - resource: contracts/notification-service/templates.yaml
  - resource: contracts/scheme-gateway/openapi.yaml
---

# Architecture

## Components

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

## The payment flow

1. `POST /api/accounts/{id}/payments` (holder only, `accounts:write`). Checks: account visible and owned, open,
   amount within the balance copy and the daily limit (every payment made today counts towards it, including
   rejected ones).
2. **Should** be screened by the fraud service here (FRD-7); not wired yet. See the fraud section for what each answer
   means.
3. On a working day before 15:30: `PaymentDispatcher.dispatch`: submit to the scheme (reference `P` + id), take the
   amount off the balance copy, post to the ledger with a new `ledgerReference`, then notify the customer.
   Otherwise: `QUEUED` with the next working day as `executionDate`; `QueuedPaymentJob.runDue()` dispatches it then.
4. Statuses: `RECEIVED`, `QUEUED`, `SUBMITTED`, `COMPLETED`, `POSTING_FAILED` (sent, ledger posting failed),
   `HELD_FOR_REVIEW` (fraud hold), `REJECTED` (scheme or fraud refused; `reasonCode`), `CANCELLED`.

## External systems

### Payment scheme gateway

- Settles an accepted instruction within about two hours.
- **Cut-off 15:30 UK** for same-day instructions; later ones are rejected with `DT01`, so the service queues them.
  Weekends and bank holidays likewise; bank holidays are not handled yet.
- **Reference** `P` + payment id, one per instruction.
- Reason codes: `AC01` wrong account number, `AC04` payee account closed, `DT01` invalid date, `DUPL` duplicate,
  `RR04` regulatory (sanctions).
- **Timeout 10 s.** A timeout means the scheme did not take the instruction; resubmit it under a new reference
  (for example `P` + id + `-R1`). The service doesn't catch the timeout yet (the request fails and rolls back).

### Fraud screening

- Answers `ACCEPT`, `REFER` or `REJECT`.
- `ACCEPT`: carry on. `REFER`: **hold**: status `HELD_FOR_REVIEW`, not sent, balance not touched, customer told it is
  being checked (`PAYMENT_UNDER_REVIEW`); the fraud team reviews within four hours (08:00 to 20:00) in its own tool.
  `REJECT`: status `REJECTED`, reason code `FRAUD`, not sent; the customer is never told why.
- **Fails closed:** no answer within **2 seconds** (`FraudScreeningUnavailableException`), or an error, is treated as
  `REFER`. Never send an unscreened payment.

### Core ledger

- System of record for money; finance's books come from it.
- `reference` is the **idempotency key**: booked once; a repeat within 24 hours returns the first booking.
- **Timeout 5 s** (`LedgerTimeoutException`). A timeout may mean booked. The dispatcher marks the payment
  `POSTING_FAILED`; operations repost from the daily exceptions report, with the same reference. **Any automatic retry
  must reuse `ledgerReference`.**
- At 02:00 the ledger sends every balance, overwriting `accounts.balance`.

### Customer notifications

- Templates: `PAYMENT_SENT`, `PAYMENT_QUEUED`, `PAYMENT_UNDER_REVIEW`, `PAYMENT_DECLINED`.
- **Last four digits only** (`accountEnding`), never a full account number or sort code: a full number is a reportable
  data-protection breach.
- **Best effort:** catch and log failures; never fail or undo a payment for one; no retries.
