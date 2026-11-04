# Accounts service: system context

*Internal wiki page, owned by the Accounts squad. The facts the code does not show: the world around the service.
Written before any task of the okf-context experiment; the OKF bundle and the AGENTS.md section (arms B and C) are
built from this page and the code.*

## What the service is for

The accounts service is the bank's system of record for the **customer's view of their current and savings
accounts**: balances, transactions, monthly statements, account notes, support cases, account closures and
**payments out**. Customers reach it through the **mobile app** and **online banking**; staff reach it through the
**back office**. It is multi-tenant: each tenant is a bank brand on the platform (acme, globex).

It does **not** hold the money. The money lives in the **core ledger**. The balance in this service is a copy: the
ledger sends every account's balance at **02:00** each night and overwrites `accounts.balance`; during the day the
service takes each payment off its own copy straight away.

## Business processes it supports

### Paying someone (a bill, rent, a friend)

1. The customer enters the payee and amount in the app. The service checks that the account is theirs and open, the
   balance, and the daily limit.
2. **Fraud screening.** The bank's policy (FRD-7, in force since 1 November 2026) is that every payment out is
   screened by the fraud service before it is sent. The client (`integration/fraud`) exists; wiring it into payments is
   on the backlog.
3. If it is a working day and before the scheme's **15:30** cut-off, the payment is sent to the **payment scheme** and
   posted to the **core ledger**, and the customer gets a "payment sent" message.
4. Otherwise it is **queued** (status `QUEUED`) for the next working day and sent by the 06:00 job. A payment is never
   refused because of the time of day.

### Monthly statements and the regulatory return

Statements are cut on the 1st of each month from the ledger's closing balances. **Regulatory reporting** builds the
monthly return to the regulator from the statements in this service, by the **5th working day** of the month. A wrong
or missing statement makes the return wrong.

### Closing an account

The holder or an admin asks; an approver decides. An account may only be closed at a **zero balance**, checked against
the ledger, not the copy here; closing with money left in it strands the customer's funds and needs a manual
remediation by operations.

### Complaints

The **complaints team** reads account notes, support cases and payment history in the back office when handling a
complaint; the regulator gives the bank **8 weeks** to answer one. Notes and payment records must therefore be
complete and never silently changed.

## External systems

### Payment scheme gateway (`integration/scheme`)

- Faster-payments style: an accepted instruction settles to the payee within about two hours.
- **Same-day cut-off 15:30 UK time.** Instructions dated today and received after it are rejected by the scheme with
  reason code `DT01`; the service therefore queues anything after the cut-off, at weekends or on a **bank holiday**,
  for the next working day.
- **Known gap:** `WorkingDays` only knows weekends. A payment queued for a bank holiday is rejected by the scheme with
  `DT01` on the day. The scheme publishes its holiday calendar; using it is on the backlog.
- The instruction reference (`P` + payment id) must be unique; the scheme rejects a reference it has seen in the last
  **30 days** with `DUPL`. Resending the same reference is therefore safe; sending a payment under a new reference
  pays twice.
- Reason codes the service sees: `AC01` wrong account number, `AC04` payee account closed, `DT01` invalid date,
  `DUPL` duplicate reference, `RR04` regulatory reason (sanctions).
- Timeout **10 seconds**. A timeout does **not** mean the scheme refused the instruction: it may have accepted it. The
  scheme has a status query by reference (`GET /v2/instructions/{reference}`), which the service doesn't use yet.

### Fraud screening service (`integration/fraud`)

- Answers `ACCEPT`, `REFER` or `REJECT` for a payment.
- `ACCEPT`: carry on.
- `REFER`: **hold** the payment for a person on the fraud team to review. It is not a rejection. The payment gets
  status `HELD_FOR_REVIEW`, is not sent and not taken off the balance, and the customer is told it is being checked.
  The fraud team reviews held payments **within four hours** (08:00 to 20:00) in its own case tool, and releases or
  cancels them there.
- `REJECT`: the payment gets status `REJECTED` with reason code `FRAUD` and is not sent. The customer is told the
  payment couldn't be made, never why (telling them would tip off a fraudster).
- **Fails closed.** If the service doesn't answer within **2 seconds**, or answers with an error, the payment is
  treated as `REFER`: held, never sent unscreened. Sending an unscreened payment breaches FRD-7.

### Core ledger (`integration/ledger`)

- The bank's system of record for money; finance's books are built from it.
- The posting `reference` is the ledger's **idempotency key**: the ledger books a reference once, and a second posting
  with the same reference within **24 hours** returns the first booking without booking again. A posting with a new
  reference is a new booking.
- Timeout **5 seconds**. A timeout does **not** mean the posting failed: the ledger may have booked it. Any retry
  must reuse the original reference; a retry under a new reference debits the customer twice.
- Payments left in `POSTING_FAILED` appear on **operations' daily exceptions report**; operations repost them by hand
  in the ledger console, using the payment's ledger reference.

### Customer notifications (`integration/notify`)

- Push and email, from templates owned by the communications team (`PAYMENT_SENT`, `PAYMENT_QUEUED`,
  `PAYMENT_UNDER_REVIEW`, `PAYMENT_FAILED`).
- **Never a full account number or sort code** in a message: the last four digits only (`accountEnding`). A full
  number in a push message is a data-protection breach that the bank must report.
- Best effort: a failed notification must never fail or undo a payment. No retries; the customer sees the status in
  the app.

## Who depends on the service

| Dependant | What they need from it |
| --- | --- |
| Customers (app, online banking) | correct balances and statuses; payments sent when promised; no double payments |
| Back-office staff (support, admins, approvers) | the account, its notes and cases; closure approvals |
| Finance reconciliation | every morning at **07:00** it matches ledger postings against the scheme's settlement report by payment reference; a payment posted twice, or sent but not posted, is a "break" that a person must investigate |
| Fraud team | held payments, with the screening result, for review within four hours |
| Regulatory reporting | complete, correct statements for the monthly return |
| Complaints team | complete notes and payment history |
| Operations | the daily exceptions report: `POSTING_FAILED` payments, and `QUEUED` payments past their execution date (the 06:00 job didn't run or failed) |

## Service levels

- Available **07:00 to 23:00** every day, target 99.9%.
- The queued-payments job runs at **06:00** on working days; if it fails, that day's queued payments miss their date
  and the customer may pay a late fee.

## Facts that come from outside the code (summary)

1. Every payment out must be screened (FRD-7); screening fails closed after 2 seconds.
2. `REFER` means hold for review within four hours, not reject.
3. `REJECT` gets reason code `FRAUD`; the customer is not told why.
4. The ledger `reference` is an idempotency key; a timed-out posting may have been booked; retries reuse the reference.
5. The scheme's cut-off is 15:30; timing never refuses a payment; bank holidays aren't handled yet (`DT01`).
6. The scheme reference must be unique for 30 days (`DUPL`); a scheme timeout may have been accepted.
7. Notifications never contain a full account number; they are best effort.
8. The balance here is a copy, overwritten from the ledger at 02:00; closures must check the ledger.
9. Finance reconciles at 07:00 by payment reference; regulatory return by the 5th working day; complaints within 8 weeks.
