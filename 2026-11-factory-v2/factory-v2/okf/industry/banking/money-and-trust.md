---
type: Playbook
title: Money and trust
description: How banking screens show money, accounts and status; tone; banking components; a glossary of plain words.
tags: [industry, banking, design]
status: draft
---

# Money and trust

People open a banking app to answer "how much do I have?", "did it go?" and "is something wrong?". Trust comes from
being exact, calm and never surprising.

## Showing money

- `£1,250.00`: pound sign, thousands separator, always two decimal places. Negative as `-£35.20` with a minus sign
  and words where it matters ("overdrawn"); never colour alone, never brackets.
- Tabular figures. In lists, amounts right-aligned. Money in is marked with a plus sign and the word or label "in",
  not only green.
- The hero amount (balance, amount being sent) is the largest thing on the screen.
- Say which balance: "Available balance" (what can be spent now, including pending) versus "Balance". If an
  overdraft is included, say so ("includes £500 arranged overdraft").
- Dates in full for anything in the future or pending: "Arrives by Friday 13 November". Times for cut-offs.

## Showing accounts and people

- Account: name, then sort code `12-34-56` and account number `1234 5678`. In lists show the last four digits
  ("ending 5678"). Card: brand-neutral, `•••• 4321`.
- Payee: the name as the customer typed it and, once checked, the name the receiving bank holds if different.
- Use fictional but well-formed details. Never a real sort code with a real account number.

## Status words

Use the same words everywhere and define them on screen when first met:

| Status | Meaning for the customer |
| --- | --- |
| Pending | we've taken it off your available balance; it hasn't finished yet |
| Sent / Paid | it has left your account |
| Scheduled | it will go on the date shown; you can still cancel |
| Declined | it didn't go; nothing was taken |
| Held for checks | we're checking it to protect you; nothing to do unless we contact you |
| Returned / Refunded | money came back |
| Frozen | the card can't be used until you unfreeze it |

Every status has an icon with a different shape as well as a colour, and words.

## Tone

Calm, plain, exact. More formal as stakes rise, never cold. No exclamation marks, no jokes about money, no blame
("you entered the wrong..."). Good news is stated plainly. Bad news comes with the next step.

## Visual trust

- One restrained brand colour, generous white space, strong alignment. Banking screens that look busy look risky.
- Red is for danger and errors only. Warnings (amber) must look different from errors and from promotions.
- No stock-photo people, no decorative charts. Illustration only where it helps (an empty state, a result).
- Security moments (approving, warnings) look like the rest of the app. Anything that looks unfamiliar looks like a
  scam.
- Do not show regulators' or protection schemes' logos in a prototype; use plain text.

## Banking components

| Component | Notes |
| --- | --- |
| Amount display | hero size, tabular, with a label saying which amount it is |
| Amount input | one big field, pound sign prefix, `inputmode="decimal"`, shows available balance beneath, validates against it and against limits |
| Account row | name, masked number, available balance; whole row selectable; selected state has a tick as well as colour |
| Payee row | initials avatar, name, masked account, "New" tag if never paid before |
| Transaction row | merchant or person, date, amount right-aligned, status tag if not complete |
| Review summary | a description list: from, to, amount, when, reference, fee; each with "Change" |
| Warning panel | icon, heading that names the risk, 2 or 3 short specific lines, a clear safe action; never dismissible by accident |
| Approval step | "Approve in the app" with what is being approved (amount and payee) repeated |
| Result panel | outcome heading, amount and payee, reference, what happens next, "Done" plus one useful next action |
| Help entry | the same "Get help" link on every screen of a journey |

## Glossary (say this, not that)

Payee -> "the person or business you're paying". Beneficiary -> never. Remittance -> "payment". Arranged overdraft
-> keep, but explain: "borrowing through your current account, up to a limit we agree". AER -> keep and explain.
Authenticate -> "approve" or "confirm it's you". Insufficient funds -> "You don't have enough money in this
account". Transaction -> "payment" or "purchase" where exact. Terminate -> "close".
