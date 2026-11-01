I’ll inspect the existing support-case API, security rules, and tests, then implement the close endpoint and run the required verification script.

I found the existing case model and conventions. I’m adding a dedicated support controller, enforcing tenant isolation before role checks, and persisting the trimmed resolution as a customer-visible comment in the same transaction as the status change.

The implementation compiles against the existing suite. I’m now running the repository’s mandated verification script, which reports the authoritative test count and failure totals.

Implemented `POST /api/support/cases/{caseId}/close`.

- Enforces tenant, assignee/admin authorization and `accounts:write`.
- Validates trimmed resolutions to 1–2000 characters.
- Closes cases atomically and records a customer-visible resolution comment.
- Returns the requested case summary.
- Returns 409 for already-closed cases.

Verification: `TESTS RUN 9, FAILED 0, ERRORS 0, SKIPPED 0`.