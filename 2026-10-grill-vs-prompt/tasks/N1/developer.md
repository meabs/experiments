# Developer brief: N1 (private: never shown to the agent)

Level: nested unknowns. rb is a rule whose answer opens a new part of the design (an approval step); rc and rd are
decisions inside that part, which only come up once the agent knows the approval step exists.

## Left out of the ticket

- **ra (in the repo): the write scope.** It changes data, so it needs `accounts:write`; without it, 403 and nothing
  changes. The README says so.
- **rb (in my head, top of mind; parent): credits over £100 wait for approval.** A credit of £100 or less is paid at
  once, as the ticket says. A credit over £100 is saved as pending (status `PENDING`) and isn't paid: the balance and
  the transactions don't change until it's approved. Still 201. Why: large goodwill payments are money out of the
  bank's pocket and need a second person.
- **rc (in my head; child of rb): how approval works.** An approver approves it with
  `POST /api/goodwill-credits/{creditId}/approve` (no body). The caller needs the `APPROVER` role in the credit's bank
  (other roles 403; another bank 404). Approving pays it: the balance goes up and the `Goodwill credit` transaction is
  booked, and the status becomes `PAID`. It returns the credit. Approving one that isn't pending: 409.
- **rd (in my head; child of rb): not your own.** Whoever asked for the credit can't approve it, even if they're an
  approver: 403, it stays pending.

## How the nesting is answered (fixed now)

- A question about limits, thresholds, approval or "anything that needs sign-off" gets rb in one or two sentences:
  "Anything over £100 needs approving before it's paid; up to £100 goes straight through." Nothing about how approval
  works.
- rc and rd are given only when the agent asks about the approval step itself (who approves, how, which endpoint,
  restrictions on approvers). A question about who approves gets both rc's role and rd ("an approver in the same bank,
  but not the person who asked for it") and, if asked or recommended differently, the endpoint.
- A recommendation that contradicts rc's endpoint path or status names is corrected with the brief's.

## Don't mind ("your call")

- Whether the response includes `status` (it may).
- Whether there's a way to reject or list pending credits: not in this ticket.
- Whether customers see goodwill credits in their transactions (they do anyway, through the transaction).
- Whether to add a test, and where.
