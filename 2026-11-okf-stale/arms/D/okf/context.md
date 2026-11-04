---
type: guide
title: System context
description: The role of accounts-service in the bank, the business processes it supports, and who depends on it.
status: stable
generated:
  by: human:accounts-squad
  at: "2026-02-27T16:00:00+00:00"
verified:
  by: human:accounts-squad
  at: "2026-03-03T10:00:00+00:00"
stale_after: "2026-06-01T00:00:00+00:00"
---

# System context

## What the accounts service does

It is the bank's system of record for the **customer's view** of their accounts: balances, transactions, monthly
statements, account notes, support cases, closures and payments out. Customers reach it through the mobile app and
online banking; staff through the back office. It sits between those channels and core banking: it does not hold the
money, which lives in the core ledger, and it sends payments through the payment scheme after the fraud service has
screened them.

## Business processes

### Paying someone (a bill, rent, a friend)

The customer enters the payee and amount in the app. The service checks the account, the balance and the daily
limit, asks the fraud service to screen the payment (`ACCEPT`, `REFER` or `REJECT`), sends accepted payments to the
payment scheme and posts them to the core ledger, and tells the customer. `REFER` means the payment is held for the
fraud team to review within **four hours**; it is not a rejection. Payments after the scheme's **15:30** cut-off, at
weekends or on bank holidays are queued for the next working day and sent by the 06:00 job; the time of day never
refuses a payment.

### Statements and the regulatory return

Statements are cut on the 1st of each month from the ledger's closing balances. Regulatory reporting builds the
monthly return to the regulator from them by the **5th working day**. A wrong or missing statement makes the return
wrong.

### Closing an account

The holder or an admin asks; an approver decides. An account may only be closed at a zero balance, **checked against
the ledger**; closing with money left in it strands the customer's funds until operations remediate by hand.

### Complaints

The complaints team reads account notes, cases and payment history; the regulator gives the bank **8 weeks** to
answer a complaint. Records must be complete and never silently changed.

## Who depends on it

| Dependant | What they need |
| --- | --- |
| Customers (app, online banking) | right balances and statuses; payments sent when promised; never paid twice |
| Back-office staff | accounts, notes, cases, closure approvals |
| Finance reconciliation | at **07:00** every morning it matches ledger postings to the scheme's settlement report by payment reference; a double posting, or a payment sent but not posted, is a break a person must investigate |
| Fraud team | held payments, with the screening result, to review within four hours |
| Regulatory reporting | complete, correct statements for the monthly return |
| Complaints team | complete notes and payment history |
| Operations | the daily exceptions report: `POSTING_FAILED` payments, and `QUEUED` payments past their date |

## Rules that come from outside the code

1. Every payment out is screened (policy FRD-7). Screening **fails closed**: no answer within 2 seconds means hold,
   never send.
2. `REFER` is a hold for review, not a rejection. `REJECT` gets reason code `FRAUD`; the customer is never told why.
3. Ledger postings are idempotent on their reference for 24 hours. A timed-out posting may have been booked; a retry
   reuses the reference, or the customer is debited twice and reconciliation breaks.
4. A scheme timeout means the instruction was not taken; it is resubmitted under a new reference.
5. Notifications never contain a full account number (last four digits only) and are best effort.
6. The balance in this service is a copy, overwritten from the ledger at 02:00.
