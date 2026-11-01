I’m reviewing the existing case, authorization, and API conventions first, then I’ll implement the close endpoint and run the offline test suite.

The existing model already stores case comments and exposes the required summary shape. I’m adding a transactional close operation that enforces tenant/assignee/admin access, trims and validates the resolution, updates status, and persists a customer-visible comment atomically.

The implementation is in place and the full offline suite passes. I also corrected the controller mapping so the new route is exactly `/api/support/cases/{caseId}/close` while preserving the existing `/api/cases` routes.

Implemented support-case closure:

- Added `POST /api/support/cases/{caseId}/close`.
- Validates trimmed resolution length (1–2000 characters).
- Allows only the assigned support user or same-tenant admin.
- Returns 404 across tenants, 403 for unauthorized same-tenant users, and 409 for already-closed cases.
- Sets status to `CLOSED`.
- Saves a customer-visible resolution comment authored by the closer.
- Existing routes and behavior remain intact.

Verified with `mvn -o -q test`.