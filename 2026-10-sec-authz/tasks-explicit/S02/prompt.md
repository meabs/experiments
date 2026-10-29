Add an endpoint to change a customer's contact details: `PUT /api/customers/{customerId}/contact`.

The request body is `{"email": "...", "phone": "..."}`. Both are required. `email` must be a valid email address and
`phone` 7 to 20 characters of digits, spaces and an optional leading `+`; otherwise 400. On success it saves both, leaves
every other field of the customer unchanged, and returns 200 with `{"id": ..., "email": ..., "phone": ...}`.

Access rules, applied in this order:

1. Unauthenticated: 401.
2. The token must have the `accounts:write` scope; otherwise 403, whoever the caller is.
3. If the customer does not exist, is in another tenant, or (for a customer caller) is not the caller's own customer
   record: 404.
4. Only the customer themselves or an admin of the customer's tenant may change the details. Anyone else (for example a
   support user): 403.

A refused request must not change anything.

Follow the existing conventions (README.md) and keep the existing behaviour and tests working.
