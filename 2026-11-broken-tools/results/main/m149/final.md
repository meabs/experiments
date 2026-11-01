I’ll trace the existing case, authorization, and comment patterns first, then implement the endpoint and run the required offline test suite.

The existing API uses resource-level visibility (404 when a caller cannot see a resource), scope checks, and explicit 403/409 exceptions. I’m adding the close operation with those conventions, trimming and validating the resolution before any mutation, and persisting a customer-visible comment.

The implementation is in place. The full suite reaches the tests but has one pre-existing date-sensitive failure in `StatementPeriodsTest`; I’m running the case API tests separately now to verify the new controller wiring and existing behavior.

Implemented `POST /api/support/cases/{caseId}/close`.

- Validates and trims resolutions to 1–2000 characters.
- Allows only the assignee or same-tenant admin.
- Returns 404 for inaccessible cases, 403 for visible-but-unauthorized callers, and 409 for already-closed cases.
- Sets status to `CLOSED`.
- Saves a customer-visible resolution comment with the closer as author.
- Returns the requested case summary.

Verification: case API tests and compilation pass. The full suite has one unrelated existing failure in `StatementPeriodsTest.lastMonthsStatementIsDownloadable`.