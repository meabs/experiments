# Developer brief: M1 (private: never shown to the agent)

Level: many unknowns, flat. Each left-out requirement is a separate topic, settled by its own question.

## Left out of the ticket

- **ra (in the repo): the write scope.** It changes data, so it needs `accounts:write`; without it, 403 and nothing
  changes. The README says so.
- **rb (in the repo): closed accounts.** A closed account's limit can't be changed: 409, nothing changes. The README's
  409 convention.
- **rc (in my head): support can only lower it.** Admins of the account's bank can set any limit. Support users
  assigned to the account can lower it (customers ring up to reduce it after a scare, and that shouldn't wait), but not
  raise it: 403, nothing changes. Raising is a credit decision, which is an admin's. Setting the same value counts as
  lowering.
- **rd (in my head): a ceiling of £5,000.** No account's limit can go above 5000, whoever sets it: 400, nothing
  changes. Why: above that, the card scheme needs a different product.
- **re (in my head): savings accounts are fixed.** A `SAVINGS` account's limit can't be changed at all: 409, nothing
  changes. Why: savings accounts have no card; their limit is part of the product.
- **rf (in my head, top of mind): an audit note.** Every change adds an internal note to the account (`internal:
  true`), written by whoever made it, giving the old and the new limit (for example "Daily limit changed from 500 to
  750"). Why: when a customer disputes a payment, staff check the notes to see what the limit was.

## Don't mind ("your call")

- The exact wording of the note, as long as it has both numbers.
- Whether to add a test, and where.
