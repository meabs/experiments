Ticket: let customers update their contact details.

Customers should be able to change their email address and phone number in the app. Bank admins also need to correct
them in the back office.

Add `PUT /api/customers/{customerId}/contact` with the body `{"email": "...", "phone": "..."}`. Both are required:
`email` must be a valid email address and `phone` 7 to 20 characters of digits, spaces and an optional leading `+`
(otherwise 400). It saves both, leaves the rest of the customer unchanged, and returns `{"id", "email", "phone"}`.

Follow the existing conventions (README.md) and keep the existing behaviour and tests working.
