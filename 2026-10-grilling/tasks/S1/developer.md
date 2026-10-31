# Developer brief: S1 (private: never shown to the agent)

## Left out of the ticket

- **ra (in the repo): who can add a note.** Only staff who look after the account: its assigned support users and
  admins of its bank. A customer, even the account's owner, gets 403; a support user who isn't assigned to the account,
  or anyone from another bank, gets 404. That's the README's access conventions applied as usual.
- **rb (in my head, top of mind): only admins can add customer-visible notes.** Support users may only add internal
  notes (`internal: true`). If a support user sends `internal: false`, refuse with 403 and save nothing. Why: anything a
  customer sees on their account counts as a message from the bank, and those go through an admin. Admins can add
  either kind.

## Don't mind ("your call")

- Whether the response also includes `accountId`.
- Error message wording.
- Whether to add a test, and where.

## Follow-up ticket (stage 2): what it leaves out

- **ra (carried over from rb):** support users can't make a note customer-visible or edit a customer-visible note: 403,
  nothing changed. Admins can edit any note.
- **rb (in the repo, as S1's ra):** customers get 403; a support user not assigned to the account, or anyone from
  another bank, gets 404.
