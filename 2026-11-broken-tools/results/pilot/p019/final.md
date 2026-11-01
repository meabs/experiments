I’m inspecting the existing case, authorization, and API patterns first, then I’ll implement the endpoint and run the mandated offline test suite.

The close flow is implemented with tenant scoping, role checks, trimmed resolution validation, status transition, and a customer-visible comment. I’m running the full offline suite now to catch mapping or persistence issues.

The targeted case API tests pass. The full suite reaches the existing `StatementPeriodsTest` failure (its fixed September 2026 expectation conflicts with the current date-based implementation); this is unrelated to the case changes. I’m doing a final diff and status check.

Implemented support case closure.

Changes:
- Added `POST /api/support/cases/{caseId}/close`.
- Validates trimmed resolution length (1–2000), returning 400 otherwise.
- Allows only the case assignee or same-tenant admin.
- Enforces tenant isolation and returns 404 for other tenants.
- Changes status to `CLOSED`.
- Saves a customer-visible resolution comment with the closer as author.
- Returns 409 when already closed without adding another comment.

`CaseApiTest` passes. The full suite has one unrelated pre-existing date-based failure in `StatementPeriodsTest`.