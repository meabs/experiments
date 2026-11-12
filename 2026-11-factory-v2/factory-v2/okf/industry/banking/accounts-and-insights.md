---
type: Playbook
title: Accounts and insights
description: Account home screens, balances, transaction lists, spending summaries and budgets in a banking app.
tags: [industry, banking, design]
status: draft
---

# Accounts and insights

## Home (account overview)

The questions, in order: how much do I have, what just happened, what is about to happen, what can I do.

- **Balance first.** The available balance is the hero. If there are several accounts, each is a row or card with
  name, masked number and balance; the main account leads. Let people hide balances.
- **Recent activity.** Three to five most recent transactions, pending ones marked, with a link to all.
- **Coming up.** Scheduled payments, direct debits and standing orders due before the next payday, with dates and a
  total; a plain warning if the balance won't cover them.
- **Quick actions.** Three or four at most (Pay, Move money, Card, Help), labelled. They are not the hero.
- **Messages.** At most one, relevant and dismissible. No promotions above the balance.
- States: loading (skeleton, not zeros), balance unavailable (say so; never show £0.00 as a stand-in), new account
  with no transactions, overdrawn.

## Transaction lists

- Group by day with a date heading ("Today", "Tuesday 10 November"). Row: who, a category or type in muted text,
  amount right-aligned, plus sign for money in.
- Pending items are marked "Pending" in words and included in the available balance.
- Tapping a row opens details: full merchant name, date and time, method (card ending, Direct Debit), reference,
  category, and actions (something wrong?, split, change category).
- Search and filter by in or out, date and category; an empty result says what was searched and how to widen it.

## Spending summaries

- Lead with one sentence in words: "You've spent £1,284.50 so far in November, £96 less than this time last month."
- Then the breakdown. Horizontal bars per category, sorted largest first, each with the label and amount in text.
  Bars beat pie and ring charts on a phone and for accuracy. Six or seven categories, then "Everything else".
- Every chart has its numbers as text and a text summary; colour is not the only way to tell categories apart
  (labels next to bars, not a separate legend).
- Compare like with like (same point in the month), and say what the comparison is.
- Categories can be wrong: let people change one and see where a number came from (tap through to the
  transactions).

## Budgets

- A budget shows spent, left and time left together: "£212 of £300 spent. £88 left for 12 days."
- Progress bars are labelled with numbers; "over budget" is stated in words and is not a red alarm. Tone: factual
  and kind, no scolding and no cheering.
- Setting a budget: suggest a figure based on recent months and say that it is a suggestion; easy to change or
  remove.

## Insight cards

One at a time, specific, with a number, a reason and an action ("Your energy Direct Debit went up £18 this month").
Never dressed-up product selling. If an insight suggests a bank product, it is labelled as such.
