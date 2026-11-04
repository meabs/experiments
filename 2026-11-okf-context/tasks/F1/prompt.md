Ticket: payment history.

Customers want to see the payments they have made from an account in the app, and the support staff and admins who
look after the account need to see them in the back office.

Add `GET /api/accounts/{accountId}/payments`. It returns the account's payments, newest first, each in the same shape
as `GET /api/payments/{paymentId}`. An optional `status` parameter keeps only the payments with that status; a status
that doesn't exist gets 400.

Follow the existing conventions (README.md) and keep the existing behaviour and tests working.
