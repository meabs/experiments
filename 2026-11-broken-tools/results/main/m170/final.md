I’ll inspect the existing case, authorization, and comment patterns, then implement the endpoint and run the mandated offline test suite.

I found the existing case model and tenant access conventions. I’m adding a dedicated close endpoint, enforcing trimmed resolution length, restricting staff by tenant/assignee, and persisting the resolution as a customer-visible comment in the same transaction.

Implemented support-case closure:

- Added `POST /api/support/cases/{caseId}/close`.
- Validates trimmed resolution length (1–2000 characters).
- Allows only the assigned support user or same-tenant admins.
- Returns 409 for already-closed cases.
- Marks the case `CLOSED` and saves a customer-visible resolution comment.
- Returns the requested case summary fields.

Verification:

- API tests pass: 25 tests.
- Full suite: 27 tests, 1 unrelated pre-existing failure in `StatementPeriodsTest.lastMonthsStatementIsDownloadable`.