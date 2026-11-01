I’ll inspect the existing support-case model, controller, security rules, and tests, then implement the endpoint and run the required Maven and verification commands.

I found the existing case entities and API conventions. I’m adding a dedicated staff endpoint with tenant-aware authorization, trimmed resolution validation, atomic status/comment persistence, and the existing 403/404/409 error mappings.

The implementation is in place and the offline Maven test run completed without reporting failures. I’m running the repository’s required verification script now to capture its authoritative test counts.

Implemented staff case closure:

- Added `POST /api/support/cases/{caseId}/close`
- Validates trimmed resolution length (1–2000 characters)
- Allows only the assigned support user or same-tenant admin
- Returns 404 across tenants, 403 for unauthorized staff/customers, and 409 for already-closed cases
- Persists a customer-visible resolution comment with the closer as author
- Updates case status to `CLOSED`

Verification:

`TESTS RUN 25, FAILED 0, ERRORS 0, SKIPPED 0`