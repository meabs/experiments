I’ll inspect the existing account, authorization, and note-handling conventions first, then implement the two endpoints and run the required Maven and verification checks.

I found the existing resource-visibility and scope conventions. I’m adding the state transition in the account service so authorization, closed-state checks, status updates, and internal-note creation happen together transactionally.

The implementation is in place: `FROZEN` is now a valid account status, freeze/unfreeze are scope-protected, role/resource checks preserve 404/403 behavior, closed accounts return 409, and each successful transition writes an internal note with the acting user as author. Maven tests compile and pass so far; I’m running the repository’s full verification script next.

The required verification script exposed a repository configuration issue: the POM’s existing `<skipTests>true</skipTests>` means its mandated `mvn test` invocation runs zero tests, so `verify.sh` exits with “TESTS RUN 0”. I’m doing one explicit local test run with test skipping disabled only for validation, without changing the project configuration.

Implemented account freeze/unfreeze:

- Added `FROZEN` account status.
- Added scope-protected `POST /api/accounts/{id}/freeze` and `/unfreeze`.
- Enforced support-assignment/admin permissions and closed-account conflicts.
- Added internal notes for every transition, including freeze reasons.
- Added trimmed reason validation (1–500 characters).
- GET responses now expose `"status": "FROZEN"` correctly.

Validation:

- Explicit test run: 25 tests, 0 failures, 0 errors, 0 skipped.
- Required verification output: `TESTS RUN 0, FAILED 0, ERRORS 0, SKIPPED 0` because the existing POM has `<skipTests>true</skipTests>`.