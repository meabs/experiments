# Developer brief: N2 (private: never shown to the agent)

Level: nested unknowns. rc is a rule whose answer opens a new part of the design (moving the money out); rd and re are
decisions inside that part, which only come up once the agent knows the money has to move.

## Left out of the ticket

- **ra (in the repo): the write scope.** It changes data, so it needs `accounts:write`; without it, 403 and nothing
  changes. The README says so.
- **rb (in the repo): only pending requests.** Approving a request that isn't `PENDING`: 409, nothing changes. The
  README's 409 convention.
- **rc (in my head, top of mind; parent): the money has to go somewhere.** An account with a balance that isn't zero
  can only be closed by moving the balance to another account: the approver says which, in the body
  `{"transferToAccountId": 1}`. If the balance isn't zero and no transfer account is given: 409, nothing changes. With
  a zero balance, no body is needed. Why: we can't close an account with the customer's money still in it.
- **rd (in my head; child of rc): where it can go.** The transfer account must be another `OPEN` account of the same
  customer, in the same bank; otherwise 400 and nothing changes.
- **re (in my head; child of rc): how the move is recorded.** It's booked as two transactions, a minus on the closing
  account and a plus on the transfer account (description `Closure transfer`; the wording is "your call"), and the closed account's balance ends
  at 0.

## How the nesting is answered (fixed now)

- A question about the balance, money left in the account, or what has to be true before closing gets rc in one or two
  sentences: "If there's money in it, it has to be moved to another account first: the approver gives the account to
  move it to (`transferToAccountId`); with money in it and no transfer account, refuse with 409." Nothing about which
  accounts are allowed or how it's booked.
- rd is given only when the agent asks which accounts the money can go to (or recommends a rule about it); re only
  when it asks how the move is recorded or booked (or recommends a way).
- A recommendation that contradicts the field name is corrected with the brief's.

## Don't mind ("your call")

- Rejecting requests: not in this ticket.
- Whether a pending closure request on the transfer account matters (it doesn't come up).
- Whether to add a test, and where.
