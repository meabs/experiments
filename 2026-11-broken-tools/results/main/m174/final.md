I’ll inspect the existing support-case API, security conventions, and tests, then implement the close endpoint and run the mandated test/verification commands.

The existing cases controller is rooted at `/api/cases`, so I’m adding a dedicated support-route controller to preserve current mappings. I’ll enforce tenant scoping, assignee/admin authorization, trimmed resolution validation, conflict handling, and customer-visible comments transactionally.

The implementation compiles and the existing Maven test suite is green so far. I’m running the repository’s required verification script now, then I’ll report the exact test totals and any caveats.

Implemented support-case closure.

- Added `POST /api/support/cases/{caseId}/close`
- Validates trimmed resolution length (1–2000)
- Allows only the assigned support user or same-tenant admin
- Returns 404 across tenants, 403 for unauthorized staff/customers
- Returns 409 for already-closed cases
- Saves the resolution as a customer-visible comment authored by the closer
- Updates status to `CLOSED`

Verification:

`TESTS RUN 25, FAILED 0, ERRORS 0, SKIPPED 0`