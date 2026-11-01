I’ll trace the existing support-case API, authorization patterns, and tests, then implement the close endpoint and run the required offline Maven suite with the test counts.

I found the existing case model and conventions. I’m adding a staff-only close route with tenant/assignee authorization, trimmed resolution validation, a persisted customer-visible comment, and an atomic OPEN→CLOSED transition.

The implementation compiles and the existing API tests execute. The full suite currently has one pre-existing failure in `StatementPeriodsTest` (27 tests total, 1 failure); I’m running the API tests separately to verify this change didn’t regress them.

Implemented staff case closure:

- Added `POST /api/support/cases/{caseId}/close`.
- Validates trimmed resolutions to 1–2000 characters.
- Allows only the assigned support user or same-tenant admin.
- Returns 404 across tenants, 403 for unauthorized same-tenant users, and 409 for already-closed cases.
- Persists the resolution as a customer-visible comment authored by the closer.
- Transitions the case to `CLOSED` and returns the requested summary fields.

Verification:

- API tests: 25 passed.
- Full suite: 27 tests, 1 pre-existing failure in `StatementPeriodsTest.lastMonthsStatementIsDownloadable`.