I’ll trace the existing support-case API, authorization, and persistence patterns, then implement the close endpoint and add focused tests before running the full offline suite.

The endpoint and persistence path are in place: authorization is tenant-scoped to the assignee or admin, resolution is trimmed and validated before mutation, and closure writes a customer-visible comment. I’m running the existing suite now to catch mapping or wiring issues.

The existing tests passed after the first implementation. I aligned the close authorization with the API’s resource-visibility convention as well: callers who cannot see a case get 404, while a customer who can see their own case receives 403 because they still lack permission to close it. I’m doing the final full run and checking the exact test totals.

Implemented support-case closure.

- Added `POST /api/support/cases/{caseId}/close`.
- Validates trimmed resolution length: 1–2000 characters.
- Allows only the assigned support user or same-tenant admin.
- Returns 404 for inaccessible cases, 403 for visible but unauthorized callers.
- Sets status to `CLOSED`.
- Saves the resolution as a customer-visible comment authored by the closer.
- Returns 409 for already-closed cases without creating another comment.

Verification: `25` tests run, `0` failures, `0` errors, `0` skipped.