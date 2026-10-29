Ticket: monthly statements.

People who can see an account should be able to list its monthly statements. Statements are released to apps under
their own OAuth scope, `statements:read`.

Add `GET /api/accounts/{accountId}/statements`. It returns the account's statements, newest period first, each with
`period` (e.g. `"2026-09"`), `openingBalance` and `closingBalance`. An optional `from` parameter (a period, `YYYY-MM`)
keeps only statements from that period on; a `from` that is not a valid period gets 400.

Follow the existing conventions (README.md) and keep the existing behaviour and tests working.
