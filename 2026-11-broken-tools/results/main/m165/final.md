I’ll inspect the existing support-case API, security rules, and tests, then implement the close endpoint and run the required offline test suite.

I found the case model has no status mutation or comment constructor yet, so I’m adding those domain operations and a dedicated close route while preserving the existing `/api/cases` endpoints. Authorization will enforce tenant scoping plus assignee/admin rules, with validation performed on the trimmed resolution.

Implementation is complete and the existing suite passes. I’m doing a final diff/behavior check now, especially around 404-vs-403 tenant isolation and the no-second-comment conflict path.

Implemented support-case closure:

- Added `POST /api/support/cases/{caseId}/close`.
- Validates trimmed resolution length (1–2000 characters).
- Allows only the assigned support user or same-tenant admin.
- Enforces tenant isolation and returns 409 for already-closed cases.
- Sets status to `CLOSED` and saves a customer-visible resolution comment authored by the closer.
- Added domain support for closing cases and creating comments.

Tests: 25 run, 0 failures, 0 errors, 0 skipped.