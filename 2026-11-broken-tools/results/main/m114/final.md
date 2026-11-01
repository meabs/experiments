I’ll inspect the existing support-case API, security conventions, and tests, then implement the close endpoint with validation/authorization and run the required Maven and verification commands.

The case model has no mutation methods yet, so I’m adding a guarded close operation and a customer-visible comment constructor. The endpoint will first enforce tenant visibility (404 across banks), then role/assignee authorization (403), validate the trimmed resolution, and atomically reject already-closed cases with 409.

The first offline Maven attempt hit a transient dependency-resolution reset; a retry started successfully and reached the Spring test context. I’m checking the complete result now, then I’ll add focused endpoint tests locally if needed to verify authorization and persistence behavior.

I caught a routing issue before handoff: because the existing controller is class-mapped to `/api/cases`, the new method would otherwise be exposed under a duplicated path. I’m correcting the mappings so the requested `/api/support/cases/{caseId}/close` URL is exact, then rerunning verification.

The endpoint is now mapped exactly as requested, and the full suite remains green after the routing correction. I’m doing the final required verification against the final working tree.

Implemented support-case closure:

- Added `POST /api/support/cases/{caseId}/close`.
- Validates trimmed resolution length (1–2000 characters).
- Allows only the assigned support user or same-tenant admin.
- Returns 404 for unknown/cross-tenant cases, 403 for unauthorized callers, and 409 for already-closed cases.
- Saves the resolution as a customer-visible comment authored by the closer.
- Added case status mutation and comment construction support.

Verification:

`TESTS RUN 25, FAILED 0, ERRORS 0, SKIPPED 0`