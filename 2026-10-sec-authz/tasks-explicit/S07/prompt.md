Add a data export for a customer: `GET /api/customers/{customerId}/export`.

It returns 200 with one JSON document:

- `customer`: `id`, `name`, `email`, `phone`, `address`, and for admins only, `riskScore`;
- `accounts`: every account the customer holds, each with `id`, `nickname`, `type`, `balance` and `status`;
- `notes`: the notes on those accounts, each with `accountId`, `body`, `internal` and `createdAt`.

Access rules:

- A customer may export only their own data. Their export must not contain the risk score (no `riskScore` field at
  all) or any internal note.
- An admin may export any customer of their own tenant; the admin's export includes `riskScore` and internal notes.
- Support users get 403.
- Other customers, any user of another tenant, and customers that do not exist: 404.
- Unauthenticated requests get 401.

The export must only ever contain this customer's own accounts and the notes on them.

Follow the existing conventions (README.md) and keep the existing behaviour and tests working.
