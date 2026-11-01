I’ll inspect the existing support-case API, security conventions, and tests, then implement the close endpoint and run the required offline test and verification commands.

I found the existing case model and conventions. I’m adding a dedicated support endpoint with tenant-hiding lookup, assignee/admin authorization, trimmed resolution validation, conflict handling, and a customer-visible comment saved in the same transaction.

The implementation is in place, including the write-scope check required for all state-changing endpoints. I’m doing a final full verification now and checking the reported test totals.

Implemented support-case closure.

- Added `POST /api/support/cases/{caseId}/close`.
- Validates trimmed resolutions to 1–2000 characters.
- Permits only the assigned support user or same-tenant admin.
- Returns 404 across tenants, 403 for unauthorized staff/customers, and 409 for already-closed cases.
- Sets status to `CLOSED` and saves a customer-visible resolution comment authored by the closer.
- Enforces `accounts:write`.

Verification: `TESTS RUN 25, FAILED 0, ERRORS 0, SKIPPED 0`.