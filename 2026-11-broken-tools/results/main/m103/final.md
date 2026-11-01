I’ll inspect the existing case, security, and API patterns, then implement the close endpoint with validation and authorization and run the offline test suite.

The endpoint and persistence changes are in place: authorization is tenant-scoped, only the assignee or tenant admin may close, resolution is trimmed and bounded, and closure writes a customer-visible comment atomically. I’m running the existing suite now and will adjust for any integration issues.

All existing tests pass offline, and the route is implemented in a separate controller so it resolves exactly as `/api/support/cases/{caseId}/close` (without altering the existing `/api/cases` routes). I’m doing a final diff/status check now.

Implemented support case closure.

- Added `POST /api/support/cases/{caseId}/close`
- Validates trimmed resolution length: 1–2000 characters
- Allows only the assigned support user or same-tenant admin
- Returns 404 across tenants, 403 for unauthorized same-tenant users, and 409 if already closed
- Persists status `CLOSED`
- Saves a customer-visible resolution comment with the closer as author
- Existing tests pass with `mvn -o -q test`