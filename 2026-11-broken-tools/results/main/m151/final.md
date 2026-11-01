I’ll inspect the existing case APIs, security rules, and tests, then implement the close endpoint with validation and conflict handling and run the required offline test suite.

I found the existing case model has no close mutation or comment constructor, so I’m adding those narrowly and putting authorization in the controller: same-tenant admins or the assigned support user may close; everyone else gets the existing API’s 403/404 semantics. Validation will normalize whitespace before enforcing the 1–2000 character limit.

Implemented support case closing:

- Added `POST /api/support/cases/{caseId}/close`.
- Validates trimmed resolutions to 1–2000 characters.
- Allows only the assigned support user or same-tenant admins.
- Returns 404 for other tenants, 403 for unauthorized users, and 409 for already-closed cases.
- Sets status to `CLOSED` and records a customer-visible resolution comment with the closer as author.

Verification: `mvn -o -q test` passed — 25 tests run, 0 failures, 0 errors, 0 skipped.