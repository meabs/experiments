I’ll inspect the existing case, security, and API patterns first, then implement the close endpoint and run the offline test suite with its test counts.

The existing model already stores case status and comments, but lacks mutation methods and a close route. I’m adding a dedicated support route so its authorization can distinguish tenant visibility (404), permitted closers (assignee/admin), and forbidden callers (403), while validating the trimmed resolution before any state changes.

Implementation is in place. The full existing suite passes (25 tests, 0 failures); I’m doing one final clean verification of the changed files and test invocation behavior before handing it over.

Implemented support-case closure:

- Added `POST /api/support/cases/{caseId}/close`.
- Validates trimmed resolutions to 1–2000 characters.
- Allows only the assigned support user or same-tenant admin.
- Returns 404 for other tenants, 403 for unauthorized same-tenant users, and 409 for already-closed cases.
- Saves the resolution as a customer-visible comment authored by the closer.
- Transitions the case to `CLOSED`.

Tests: 25 run, 0 failures, 0 errors.