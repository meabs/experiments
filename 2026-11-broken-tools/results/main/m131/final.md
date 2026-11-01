I’ll inspect the existing support-case API, security conventions, and tests, then implement the close endpoint and run the required verification.

I found the existing case model and security patterns. I’m adding the close operation transactionally, with tenant-scoped lookup, assignee/admin authorization, conflict handling before any mutation, and a customer-visible comment.

I caught a routing detail before finalizing: the existing controller has a class-level `/api/cases` prefix, so the new `/api/support/cases/...` operation must live in a separate controller to avoid an unintended combined path.

Implemented support-case closure:

- Added `POST /api/support/cases/{caseId}/close`.
- Validates trimmed resolutions to 1–2000 characters.
- Allows only the assigned support user or same-tenant admin.
- Returns 404 for other tenants, 403 for unauthorized users, and 409 for already closed cases.
- Marks the case `CLOSED` and records a customer-visible resolution comment authored by the closer.
- Returns the requested case summary fields.

Verification passed:

`TESTS RUN 25, FAILED 0, ERRORS 0, SKIPPED 0`