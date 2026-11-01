I’ll inspect the existing support-case API, security checks, persistence model, and tests, then implement the close endpoint and run the required test/verification commands.

The existing case model has no close mutation or comment constructor, so I’m adding those narrowly, then a dedicated `/api/support/cases` controller that enforces tenant, role, assignee, status, and trimmed-resolution rules inside one transaction.

The implementation compiles and all existing tests pass. I’m doing a final diff review now to catch any API-convention mismatch (especially status/authorization ordering) before handing it over.

Implemented support-case closure:

- Added `POST /api/support/cases/{caseId}/close`.
- Enforced tenant, assignee/admin, scope, and status rules.
- Added trimmed 1–2000 character resolution validation.
- Saves the resolution as a customer-visible comment authored by the closer.
- Returns the requested case summary.
- Added 409 handling for already-closed cases.

Verification completed:

`TESTS RUN 25, FAILED 0, ERRORS 0, SKIPPED 0`