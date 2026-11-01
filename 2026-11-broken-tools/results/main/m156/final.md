I’ll inspect the existing case/support API, security conventions, and tests, then implement the endpoint and run the mandated offline test suite.

The existing model already has case assignees and comments, but lacks mutation methods. I’ll add a transactional close operation that first enforces tenant/assignee visibility, then checks `CLOSED`, trims and validates the resolution, writes a customer-visible comment, and changes status atomically.

The implementation compiles under the project’s default Maven invocation, but this repository sets `skipTests=true` in its POM, so that command executes zero tests. I’m rerunning with only that property overridden to verify the actual suite and test counts.

The route is now correctly isolated at `/api/support/cases/{caseId}/close` (the existing `/api/cases` controller mapping would otherwise prepend the wrong path). Tests remain green after this correction.

Implemented support case closure:

- Added `POST /api/support/cases/{caseId}/close`.
- Validates trimmed resolutions to 1–2000 characters.
- Allows only the assigned support user or same-tenant admins.
- Returns 404 for inaccessible cases and 409 for already closed cases.
- Sets status to `CLOSED`.
- Saves the resolution as a customer-visible comment authored by the closer.

Verification: 25 tests ran, with 0 failures and 0 errors.