---
type: Playbook
title: Cards and security
description: Freezing a card, reporting it lost or stolen, replacement, unrecognised transactions and approval steps in a UK banking app.
tags: [industry, banking, cards, security]
status: draft
sources:
  - title: Payment Services Regulations 2017, regulations 72 to 77 (notification, liability for unauthorised transactions)
    resource: https://www.legislation.gov.uk/uksi/2017/752/contents
    checked: not fetched; the £35 figure and next-business-day refund are from the author's knowledge - check current rule
---

# Cards and security

Someone whose card is missing is stressed and in a hurry. The first screen must let them make the card safe in one
action, then sort out the rest.

## Freeze, lost, stolen

| Situation | What they need | Design |
| --- | --- | --- |
| "I can't find it" | stop it being used, reversibly | **Freeze** as an immediate switch on the card screen; state changes at once with words ("Frozen. It can't be used for purchases or cash."); unfreeze the same way |
| "It's lost for good" | cancel and replace | report lost: cancels the card permanently (say so before they confirm), orders a replacement |
| "It was stolen" or "someone used it" | cancel, replace, check payments, feel safe | as lost, plus review recent transactions and mark any they don't recognise; reassurance about getting money back; how to contact the fraud team now |

- Ask which situation first, in the customer's words, not "select card status".
- Make the safe action reachable in one or two taps from the card screen and from help.
- Cancelling is permanent: confirm with the consequences (card stops working now, including in digital wallets
  unless stated otherwise; regular payments set up on the card will need the new details).
- Say what keeps working: the account, transfers, direct debits, and (if true for the product) a virtual card in the
  phone's wallet.

## Replacement

Confirm the delivery address (masked, with a route to change it that needs approval), when it arrives ("in 3 to 5
working days"), that the PIN stays the same or how to see it, and whether a digital card is available straight away.

## Unrecognised transactions

- Show recent card transactions with clear merchant names, dates and amounts; let the customer mark the ones they
  don't recognise; include "I'm not sure" help (merchant trading names, pending amounts, subscriptions).
- Say what happens next and when: the bank looks into it; for payments the customer did not authorise, the bank must
  generally refund by the end of the next working day unless it suspects fraud by the customer; the customer may be
  liable for up to £35 of losses before reporting in some cases (check current rule). Do not promise an outcome on
  screen; do say "tell us as soon as you can".
- Give the fraud phone number and say the bank will never ask for a PIN or full password.

## Approving and signing in

- Approval steps repeat what is being approved. Offer device biometrics or a passcode; never a memory puzzle; allow
  paste and password managers.
- Session time-out: warn first, let them stay signed in, keep what they typed.
- Sensitive details (full card number, PIN) are shown only on request, after approval, and hide again.

## Result screens

State the card's status in words, what was ordered, the date, what the customer should do now (nothing, or "update
your card details with these subscriptions"), and a reference.
