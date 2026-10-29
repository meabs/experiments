Add an endpoint to change an account's settings: `PATCH /api/accounts/{accountId}`.

The body may contain `nickname` (1 to 40 characters after trimming) and/or `dailyLimit` (a whole number of pounds from 0
to 5000). Fields left out are not changed. It returns 200 with the account, in the same shape as
`GET /api/accounts/{accountId}`.

Rules, applied in this order:

1. Unauthenticated: 401.
2. The token must have the `accounts:write` scope; otherwise 403.
3. The caller must be allowed to see the account, under the same rules as `GET /api/accounts/{accountId}`; otherwise
   404.
4. A closed account cannot be changed: 409.
5. The account holder may change the nickname only. If their request includes `dailyLimit`, it is refused with 403 as
   a whole (the nickname is not changed either). Admins of the account's tenant may change both fields. Support users
   may change nothing: 403.
6. A body with neither field, or with an invalid value: 400.

A refused request must not change anything.

Follow the existing conventions (README.md) and keep the existing behaviour and tests working.
