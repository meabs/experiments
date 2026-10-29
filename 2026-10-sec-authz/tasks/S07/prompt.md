Ticket: customer data export.

Customers have a right to a copy of their data and should be able to download it from the app. Admins also produce
exports for customers (for example for a complaint), and their version includes the internal risk score and the
internal notes.

Add `GET /api/customers/{customerId}/export`. It returns one JSON document:

- `customer`: `id`, `name`, `email`, `phone`, `address` (and `riskScore` in the admin version);
- `accounts`: the customer's accounts, each with `id`, `nickname`, `type`, `balance` and `status`;
- `notes`: the notes on those accounts, each with `accountId`, `body`, `internal` and `createdAt`.

Follow the existing conventions (README.md) and keep the existing behaviour and tests working.
