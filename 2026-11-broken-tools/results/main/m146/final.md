I’ll inspect the existing support-case API, security conventions, and tests, then implement the close endpoint and run the required verification suite.

I found the existing case model and security conventions. I’m adding the close operation with tenant/resource visibility checks, status conflict handling, trimmed resolution validation, and a customer-visible comment authored by the closer.

I caught an important routing detail during verification: because the existing controller is rooted at `/api/cases`, the new route must live in a separate controller to expose exactly `/api/support/cases/{caseId}/close`. I’m correcting that before final validation.

Implemented support-case closure:

- Added `POST /api/support/cases/{caseId}/close`.
- Enforced tenant, assignee, admin, and customer permissions.
- Added trimmed 1–2000 character resolution validation.
- Added `CLOSED` status transition and conflict handling for already-closed cases.
- Persisted customer-visible resolution comments with the closer as author.
- Added response fields matching the requested case summary.

Validation results:

- Tests with `-DskipTests=false`: `TESTS RUN 25 FAILED 0 ERRORS 0 SKIPPED 0`
- Required `scripts/verify.sh` output: `TESTS RUN 0, FAILED 0, ERRORS 0, SKIPPED 0` (the repository POM sets `skipTests=true`, so the script exits with “verify: no tests ran”).