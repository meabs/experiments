I’ll inspect the existing case, authorization, and API patterns first, then implement the close endpoint, add focused tests, run the full verification script, and report the exact test counts.

The existing model has cases and comments but no mutation methods, so I’m wiring the close operation into the current controller conventions. I’ll preserve tenant concealment (404 across banks), return 403 for visible-but-unauthorized staff/customers, and validate the trimmed resolution explicitly so surrounding whitespace doesn’t incorrectly count toward the 2000-character limit.

The implementation is in place: same-tenant admins or the exact assignee can close, the case transitions once, and a customer-visible comment is written with the closer as author. I’m now checking compilation and the repository’s required full verification output, then I’ll do a targeted API exercise for the new route if needed.

Implemented support-case closure.

- Added `POST /api/support/cases/{caseId}/close`.
- Enforces tenant, assignee/admin, scope, and status rules.
- Validates trimmed resolutions to 1–2000 characters.
- Saves a customer-visible resolution comment authored by the closer.
- Returns the requested case summary.

Verification:

`TESTS RUN 9, FAILED 0, ERRORS 0, SKIPPED 0`

Also ran the existing `CaseApiTest`: 6 tests passed.