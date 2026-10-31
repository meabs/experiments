# Developer brief: L2 (private: never shown to the agent)

## Left out of the ticket

- **ra (in the repo): the write scope.** It changes data, so it needs `accounts:write`; without it, 403 and nothing
  changes. The README says so.
- **rb (in the repo): other banks.** A case in another bank answers 404, as if it didn't exist. README conventions.
- **rc (in my head, top of mind): who a case can go to.** The new assignee must be a support user assigned to the case's
  account (`support_assignments`); otherwise 400 and nothing changes. Why: support users can only open the accounts
  they're assigned to, so anyone else would get a case they can't work on.
- **rd (in my head; guessable, see the amendment log): the current assignee can hand a case over.** Not only admins: the support user who currently has
  the case can reassign it, for example before going on leave. Other support users can't (404, they can't see the
  case). Admins can reassign any case in their bank.

## Don't mind ("your call")

- Whether reassigning records who did it or when.
- Reassigning a case to the user who already has it (fine either way).
- Unassigning (null assignee): not needed now.
- Whether to add a test, and where.

## Follow-up ticket (stage 2): what it leaves out

- **ra (carried over from rc):** the assignee must be assigned to every listed case's account; otherwise 400 and no case
  changes.
- **rb (in the repo):** a case id that doesn't exist or is in another bank answers 404 and no case changes (the README:
  a change request is refused as a whole).
- **rc (in the repo, as L2's ra):** the `accounts:write` scope: 403 without it, nothing changes.
