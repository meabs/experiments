I’ll inspect the existing case, authorization, and API patterns, then implement the close endpoint with validation and tests, and finish by running the required verification script.

The existing model already has assignees, comments, tenant-aware users, and the API’s 400/403/404/409 handlers. I’m wiring the new support-only route into those conventions, including atomic status/comment persistence and post-trim resolution validation.

The implementation is in place and the offline Maven run has now started successfully after a transient dependency-resolution hiccup. I’m checking the final test count and the repository verification script next.

Implemented support-case closure:

- Added `POST /api/support/cases/{caseId}/close`.
- Validates trimmed resolutions to 1–2000 characters.
- Allows only the assignee or same-tenant admin.
- Returns 404 across tenants, 403 for unauthorized users, and 409 for already-closed cases.
- Saves a customer-visible resolution comment authored by the closer.
- Sets case status to `CLOSED`.

Verification passed:

`TESTS RUN 25, FAILED 0, ERRORS 0, SKIPPED 0`