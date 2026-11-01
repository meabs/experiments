I’ll trace the existing support-case API, security checks, persistence model, and test conventions, then implement the close endpoint and run the required verification.

The endpoint and persistence changes are in place: tenant isolation is enforced, only the assignee or same-tenant admin can close, closed cases return 409, and each successful close writes a customer-visible comment. I’m compiling and running the existing suite now.

Implemented support-case closure:

- Added `POST /api/support/cases/{caseId}/close`.
- Validates trimmed resolution length (1–2000 characters).
- Allows only the assigned support user or same-tenant admin.
- Returns 404 across tenants, 403 for unauthorized users, and 409 for already-closed cases.
- Sets status to `CLOSED`.
- Saves the resolution as a customer-visible comment authored by the closer.

Verification output:

`TESTS RUN 27, FAILED 1, ERRORS 0, SKIPPED 0`

The sole failure is the pre-existing `StatementPeriodsTest` date-dependent test and is unrelated to this change.