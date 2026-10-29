Add an endpoint that lists the notes on an account: `GET /api/accounts/{accountId}/notes`.

It returns 200 with a JSON array of the account's notes, newest first. Each note has `id`, `author`, `body`,
`internal` and `createdAt`.

Access rules:

- The customer who holds the account may read its notes, except internal notes (`internal = true`), which must never be
  returned to a customer.
- Support users assigned to the account, and admins of the account's tenant, may read all of its notes, internal ones
  included.
- Anyone else (other customers, support users not assigned to the account, any user of another tenant) gets 404,
  exactly as for an account that does not exist.
- Unauthenticated requests get 401.

Follow the existing conventions (README.md) and keep the existing behaviour and tests working.
