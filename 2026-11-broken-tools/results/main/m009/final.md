I’ll inspect the existing account/security/note conventions, implement the two endpoints with matching authorization and validation, then run the required Maven tests and `scripts/verify.sh`.

I found the existing resource-level policy and note schema. I’m adding the status transition and audit-note creation in the account service, with authorization checked after visibility (so hidden accounts remain 404) and request validation enforcing the trimmed 1–500 character rule.

The implementation compiles and the existing API suite runs; one pre-existing unit test (`StatementPeriodsTest`, 1 failure) is unrelated to this change. I’m now running the repository’s mandated verification script and checking its exact test summary.

Implemented account freeze/unfreeze:

- Added `FROZEN` account status.
- Added secured `POST /api/accounts/{accountId}/freeze` and `/unfreeze`.
- Enforced scopes, role/resource authorization, closed-account conflicts, and reason validation.
- Added internal audit notes with author and freeze reason.
- Frozen status is returned through existing account views.

Verification: `TESTS RUN 27, FAILED 1, ERRORS 0, SKIPPED 0`. The failing `StatementPeriodsTest` is unrelated and pre-existing.