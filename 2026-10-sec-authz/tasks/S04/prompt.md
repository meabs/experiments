Ticket: customer search for the back office.

Support staff and admins need to find customers by name or email.

Add `GET /api/customers/search?q=...`. It returns the matching customers sorted by name, each with only `id`, `name`
and `email`. A customer matches if `q` appears in their name or email, ignoring case. `q` must have at least 2
characters after trimming spaces (otherwise 400).

Follow the existing conventions (README.md) and keep the existing behaviour and tests working.
