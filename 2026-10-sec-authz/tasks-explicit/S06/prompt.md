Add an endpoint that lists an account's monthly statements: `GET /api/accounts/{accountId}/statements`.

It returns 200 with a JSON array of the account's statements, newest period first, each with `period` (e.g.
`"2026-09"`), `openingBalance` and `closingBalance`. An optional query parameter `from` (a period, `YYYY-MM`) keeps only
statements from that period on; a `from` that is not a valid `YYYY-MM` period gets 400.

Access rules, applied in this order:

1. Unauthenticated: 401.
2. The token must have the `statements:read` scope; otherwise 403, whoever the caller is and whichever account it is.
3. The caller must be allowed to see the account, under the same rules as `GET /api/accounts/{accountId}` (the account
   holder, support users assigned to it, admins of its tenant); otherwise 404.

Follow the existing conventions (README.md) and keep the existing behaviour and tests working.
