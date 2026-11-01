I’ll inspect the existing support-case API, security rules, and tests, then implement the close endpoint and add focused coverage before running the mandated Maven test command.

I found the existing case model has no mutation/comment constructors, so I’m adding the smallest domain methods needed, plus a transactional close operation that first applies the API’s visibility rules and then checks the caller’s closing role.

I caught a routing issue before testing: because the existing controller is rooted at `/api/cases`, adding the new method there would produce the wrong URL. I’m moving the close operation into its own controller so the public route is exactly `/api/support/cases/{caseId}/close`.

Implemented support-case closure.

- Added `POST /api/support/cases/{caseId}/close`
- Validates trimmed resolution length (1–2000), returning 400 otherwise
- Allows only the assigned support user or same-tenant admin
- Returns 404 for inaccessible cases and 409 for already-closed cases
- Stores the resolution as a customer-visible comment authored by the closer
- Updates case status to `CLOSED`

Tests: `25` run, `0` failures, `0` errors.