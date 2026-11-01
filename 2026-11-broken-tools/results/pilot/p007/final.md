I’ll trace the existing case, authorization, and comment patterns, then implement the endpoint and run the mandated offline test suite.

The existing API uses 404 for resources outside a caller’s visibility and 403 for visible-but-disallowed actions, plus 409 for invalid state. I’m applying that model here: same-tenant unauthorized staff/customers get 403, cross-tenant cases are hidden as 404, and closure plus comment are committed in one transaction.

Implementation is complete and the full offline Maven suite passes. The endpoint validates trimmed resolution length, enforces tenant/assignee-or-admin access, atomically marks the case closed, and records a customer-visible comment authored by the caller.

Implemented `POST /api/support/cases/{caseId}/close`.

- Validates trimmed resolution length: 1–2000 characters.
- Allows only the case assignee or same-tenant admin.
- Returns 404 for missing/cross-tenant cases, 403 for unauthorized callers, and 409 if already closed.
- Sets status to `CLOSED`.
- Saves a customer-visible resolution comment authored by the closer.
- Returns the requested case summary fields.

Verified with `mvn -o -q test` (all tests pass).