I’ll inspect the existing case, security, and API patterns, then implement the close endpoint and run the required offline test suite.

The existing model has immutable case status and a comment entity without a convenience constructor, so I’m adding a transactional close operation that trims/validates the resolution, enforces tenant and assignee/admin access, updates status, and persists a customer-visible comment atomically.

The implementation compiles, and the existing case API tests pass. The full suite reaches one pre-existing asynchronous broker test failure (`BalanceAlertPublisherTest`), unrelated to these changes; I’ll report that separately.

Implemented support-case closure:

- Added `POST /api/support/cases/{caseId}/close`
- Validates trimmed resolutions to 1–2000 characters
- Allows only the assigned support user or same-tenant admins
- Returns 404 for inaccessible cases, 403 for visible but unauthorized callers
- Sets status to `CLOSED`
- Saves a customer-visible resolution comment with the closer as author
- Returns 409 for already-closed cases
- Added case status mutation and comment construction support

Verification:

- Existing `CaseApiTest` passes.
- `mvn -o -q -DskipTests package` passes.
- Full suite has one unrelated pre-existing failure in `BalanceAlertPublisherTest`.