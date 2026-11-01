I’ll trace the existing support-case model, authorization, and endpoint conventions, then implement the close flow and run the mandated tests plus `scripts/verify.sh`.

I found the existing case controller, JPA entities, and API exception conventions. I’m adding the close operation under `/api/support/cases/{caseId}/close`, with tenant-aware authorization, trimmed resolution validation, status transition, and a customer-visible comment in one transaction.

The implementation compiles and the existing Maven test command completed successfully. I’m now running the repository’s required verification script, which reports the exact test totals and catches any integration-level issues.

Implemented support-case closure:

- Added `POST /api/support/cases/{caseId}/close`.
- Validates trimmed resolutions to 1–2000 characters.
- Allows only the assigned support user or same-tenant admins.
- Returns 404 across tenants, 403 for unauthorized same-tenant users, and 409 for already-closed cases.
- Sets status to `CLOSED` and saves a customer-visible resolution comment authored by the closer.

Tests: `mvn -o -q -DskipTests=false test` passed — 25 run, 0 failed.

`scripts/verify.sh` reported: `TESTS RUN 0, FAILED 0, ERRORS 0, SKIPPED 0` because the project’s default `skipTests=true` prevents its Maven invocation from running tests.