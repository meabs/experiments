Ticket: cancel a payment that hasn't gone yet.

Customers sometimes change their mind about a payment that is still waiting to be sent.

Add `POST /api/payments/{paymentId}/cancel`. A payment that is waiting for its execution date (`QUEUED`) becomes
`CANCELLED` and is never sent. It returns the payment in the same shape as `GET /api/payments/{paymentId}`. A payment
in any other status can't be cancelled. Only the account holder can cancel their payments.

Follow the existing conventions (README.md) and keep the existing behaviour and tests working.
