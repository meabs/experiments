---
type: guide
title: System information
description: What accounts-service is, how it is built, run and tested, and its key pitfalls.
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
  - resource: README.md
---

# System information

## What it is

`accounts-service` is the bank's system of record for the customer's view of their current and savings accounts:
balances, transactions, statements, notes, support cases, closures, and **payments out**. Customers use it through
the mobile app and online banking, staff through the back office. It is multi-tenant (each tenant is a bank brand:
`acme`, `globex`). Owner: the Accounts squad. Service level: available 07:00 to 23:00 every day, target 99.9%.

It does **not** hold the money: the core ledger does. See [architecture](/architecture.md) and
[system context](/context.md).

## Build, run, test

- Spring Boot 3.5, Java 21, Maven, H2 in memory with fixtures in `src/main/resources/data.sql`.
- `mvn -o -q test` runs everything offline.
- Tests are API tests over MockMvc with real signed tokens; `ApiTest` is the base class. The four external systems are
  fakes in tests (`TestIntegrations`): `FakeScheme`, `FakeFraudScreening` (answers `ACCEPT` unless told otherwise;
  `unavailable()` simulates a timeout), `FakeLedger` (books each reference once, like the real ledger;
  `timeOutNext(n, applied)` simulates timeouts before or after booking) and `FakeNotifications`.
- The clock is a bean (`ClockConfig`, UK time). Tests use `MutableClock`, which starts on **Tuesday 6 October 2026,
  10:00 UK time**; payments in `data.sql` are dated relative to that.

## Key pitfalls

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
5. **A scheme timeout means the scheme did not take the instruction.** Resubmit it under a new reference (the
   scheme reference is `P` + payment id; add a suffix such as `-R1`). Today a
   scheme timeout is not handled: the request fails and the transaction rolls back, losing the local record of a
   payment the scheme may have taken.
6. **Notifications never contain a full account number or sort code**: last four digits only (`accountEnding`).
   Notifications are best effort: a failure must never fail or undo a payment.
7. **Times are UK time.** Use the injected `Clock`, never `now()` without it, or tests and the cut-off break.
8. **Access rules** (README): 404 for anything the caller may not see, 403 for not allowed, 409 for the wrong state.
   Only the account holder can pay from an account. Never cross tenants.
