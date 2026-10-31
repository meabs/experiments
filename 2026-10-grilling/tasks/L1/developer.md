# Developer brief: L1 (private: never shown to the agent)

## Left out of the ticket

- **ra (in the repo): the write scope.** Both endpoints change data, so they need the `accounts:write` scope; without
  it, 403 and nothing changes. The README says so.
- **rb (in the repo): closed accounts.** A closed account can't be frozen or unfrozen: 409, and nothing changes. The
  README's 409 convention.
- **rc (in my head): who can do which.** Support users assigned to the account can freeze it, so anyone looking after
  it can stop fraud quickly. Only admins can unfreeze, because lifting a freeze needs the fraud team's sign-off, which
  is an admin. A support user trying to unfreeze gets 403. Admins can do both.
- **rd (in my head, top of mind): an audit trail in the notes.** Every freeze and unfreeze adds an internal note to the
  account (`internal: true`), written by whoever did it. The freeze note includes the reason. Why: staff look at the
  notes to see what happened to an account, and the fraud team needs the trail.

## Don't mind ("your call")

- Freezing an account that's already frozen, or unfreezing one that isn't (409 or leave it as it is, either is fine).
- The exact wording of the audit notes, as long as the freeze note contains the reason.
- Whether a frozen account blocks other actions (closure requests and so on): not in this ticket.
- Whether to add a test, and where.

## Follow-up ticket (stage 2): what it leaves out

- **ra (carried over from rd):** every account the bulk freeze freezes gets an internal note with the reason, written by
  the caller.
- **rb (in the repo, as L1's ra):** the `accounts:write` scope: 403 without it, nothing changes.
