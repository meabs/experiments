Add a customer search for staff: `GET /api/customers/search?q=...`.

It returns 200 with a JSON array of matching customers, sorted by name, each with only `id`, `name` and `email`. A
customer matches if `q` appears in their name or email, ignoring case.

Rules:

- Only support users and admins may search; anyone else gets 403.
- `q` is required and must have at least 2 characters after trimming spaces; otherwise 400.
- Only customers of the caller's own tenant are ever returned. The tenant always comes from the caller's token, never
  from the request.
- Admins find any customer in their tenant. Support users only find customers who hold at least one account assigned
  to them.
- The results must not include any other customer data (no phone, address or risk score).

Follow the existing conventions (README.md) and keep the existing behaviour and tests working.
