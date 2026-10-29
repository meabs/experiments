Ticket: show the notes on an account.

Staff leave notes on accounts. Account holders should be able to see the notes on their accounts in the app, and the
support staff and admins who look after an account need to see them in the back office.

Add `GET /api/accounts/{accountId}/notes`. It returns the account's notes, newest first, each with `id`, `author`,
`body`, `internal` and `createdAt`.

Follow the existing conventions (README.md) and keep the existing behaviour and tests working.
