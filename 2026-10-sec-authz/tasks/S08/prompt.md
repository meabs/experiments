Ticket: account settings.

Customers want to rename their accounts in the app. Admins also need to change an account's daily limit.

Add `PATCH /api/accounts/{accountId}`. The body may contain `nickname` (1 to 40 characters after trimming) and/or
`dailyLimit` (a whole number of pounds from 0 to 5000); fields left out are not changed. A body with neither field, or
with an invalid value, gets 400. Closed accounts cannot be changed (409). It returns the account in the same shape as
`GET /api/accounts/{accountId}`.

Follow the existing conventions (README.md) and keep the existing behaviour and tests working.
