I’ll inspect the existing support-case API, security checks, and tests, then implement the close endpoint and add focused coverage.

I found the existing case model and security conventions. I’m adding a dedicated staff close route, enforcing tenant visibility and assignee/admin authorization, and persisting the trimmed resolution as a customer-visible comment in the same transaction.

The implementation is in place and the existing suite passes offline. I’m doing a final diff/behavior review now, especially around validation order and tenant masking (404 versus 403).

Implemented support-case closing.

- Added `POST /api/support/cases/{caseId}/close`
- Validates trimmed resolution length: 1–2000 characters
- Allows only the assigned support user or same-tenant admin
- Returns 404 across tenants, 403 for unauthorized same-tenant users, and 409 for already-closed cases
- Sets status to `CLOSED`
- Saves a customer-visible resolution comment authored by the closer
- Existing tests pass with `mvn -o -q test`