I’ll inspect the existing support-case API, security conventions, and tests, then implement the close endpoint and add focused coverage before running the mandated offline Maven test suite.

The existing case controller is customer-facing at `/api/cases`; I’m adding the staff action as a separate `/api/support/cases/{caseId}/close` route, with tenant-safe lookup, assignee/admin authorization, transactional status/comment persistence, and trimmed-length validation.

Implementation is in place. The offline Maven run is currently blocked before compilation because the local repository cannot read the Spring Boot 3.5.6 descriptor (`Connection reset`), so I’m doing a source-level review and will retry the required command once.

Implemented support-case closure:

- Added `POST /api/support/cases/{caseId}/close`.
- Enforces tenant, assignee/admin, scope, and status rules.
- Validates trimmed resolution length (1–2000 characters).
- Sets status to `CLOSED` and saves a customer-visible resolution comment.
- Returns the requested case summary.

Validation: `mvn -o -q test` passed — 25 tests, 0 failures, 0 errors.