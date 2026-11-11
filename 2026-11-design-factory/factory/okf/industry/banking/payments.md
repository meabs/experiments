---
type: Playbook
title: Payments
description: Paying a person or business from a UK current account - steps, new payees, Confirmation of Payee results, approval, results, pending and failed payments, scam protection.
tags: [industry, banking, payments]
status: draft
sources:
  - title: Payment Systems Regulator, APP scams - frequently asked questions for consumers
    resource: https://psr.org.uk/our-work/app-scams/frequently-asked-questions-for-consumers
    checked: 11 November 2026, by search summary (Confirmation of Payee results; reimbursement limit)
  - title: Payment Services Regulations 2017 and FCA guidance on strong customer authentication
    resource: https://www.legislation.gov.uk/uksi/2017/752/contents
    checked: not fetched; written from the author's knowledge
---

# Payments

## The conventional order

1. Choose who to pay (existing payee, or add new). 2. For a new payee: name, sort code, account number, personal or
business. 3. Name check (Confirmation of Payee). 4. Amount, reference, when (now or a date); the paying account and
its available balance are visible. 5. Review. 6. Approve (confirm it's you). 7. Result.

Amount before payee is also common for small payments to existing payees. Keep to one order within a product.

## Confirmation of Payee (name check)

Before a first payment to a new payee, the bank asks the receiving bank whether the name matches the account. Four
results; each needs its own state:

| Result | What the customer should be told | Design |
| --- | --- | --- |
| Match | the name matches the account | quiet confirmation (tick and words), carry on |
| Close match | the name is similar; show the name the account is actually in | show the returned name, offer "Use this name" or "Edit details"; carrying on with the typed name is a deliberate choice |
| No match | the name does not match; this can be a sign of a scam or a mistake | strong warning; default action is to go back and check with the person by a trusted route; continuing is possible but deliberate, with the risk stated (the money may not be recoverable) |
| Check unavailable | the check couldn't be done (the other bank doesn't support it or didn't answer) | say so plainly; advise checking the details with the payee before continuing |

Never show "match" styling for anything but a match. Never auto-correct details silently.

## Scam warnings

Most fraud losses on bank transfers are payments the customer was tricked into making. Good warnings:

- appear at the risky moment (new payee, large or unusual amount, a no-match result), not on every payment;
- are specific to the purpose. Ask "What's this payment for?" (paying a friend, buying something, an investment,
  moving money to a "safe account", paying a bill or tradesperson) and tailor two or three lines to the answer;
- name the trick ("A bank or the police will never ask you to move money to keep it safe");
- give a safe action ("Stop and call us on the number on your card") as prominent as carrying on;
- look unlike marketing and are not dismissed by the same thumb position as "Continue";
- do not blame or lecture.

Customers tricked into sending a Faster Payment can usually claim reimbursement from their bank, up to a limit
(£85,000 when the rule began in October 2024; check current rule) with exceptions. Do not promise outcomes on
screen; do say how to report a scam quickly.

## Approving (strong customer authentication)

Banks must confirm it is the customer for electronic payments, with exemptions (for example trusted payees and some
low-value payments). The approval must be tied to the specific amount and payee, so the approval step repeats both.
In a prototype, simulate with a labelled step ("Approve with Face ID or your passcode" as a button) and never
collect a real credential.

## Results: say where the money is

| Outcome | Tell the customer |
| --- | --- |
| Sent | amount, to whom, reference, "usually arrives within 2 hours" (Faster Payments are often immediate but not guaranteed) |
| Scheduled | the date, that it can be cancelled until then, where to find it |
| Held for checks | it has not gone yet, we may contact you, what to expect and when; do not send it again |
| Pending or unknown (lost connection, time-out) | we don't know yet whether it went; do not try again; where to check; we'll tell you |
| Declined | nothing has left the account, why in plain words (not enough money, daily limit, details rejected), what to do |

Double-send protection: lock the button after the first press; after a time-out show the pending state, not the form.

## Limits, cut-offs and details

- Show the daily payment limit when the amount is near or over it, with what to do.
- A reference field (up to 18 characters) with a hint about what the payee needs to see.
- Future-dated and recurring payments: show the first date, how often, the end, and how to cancel.
- New payee added: say so, and that future payments to them won't need the name check.
