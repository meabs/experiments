I’ll trace the existing account, authorization, and internal-note conventions first, then implement the two endpoints and run the required offline tests plus `scripts/verify.sh`.

The implementation is in place: `FROZEN` is now a persisted account state, mutation methods enforce visibility/role/scope/state rules transactionally, and each successful action writes an internal note with the caller as author. I’m checking the full suite now; one pre-existing unit test is already showing an unrelated failure.

Implemented account freeze/unfreeze:

- Added `FROZEN` account status.
- Added scoped `POST /api/accounts/{id}/freeze` and `/unfreeze` endpoints.
- Enforced support-assignment/admin permissions, closed-account conflicts, and reason validation.
- Added internal notes for each action with author and freeze reason.
- Account responses now expose `status: "FROZEN"`.

Verification:

`TESTS RUN 27, FAILED 1, ERRORS 0, SKIPPED 0`

The single failure is the pre-existing unrelated `StatementPeriodsTest.lastMonthsStatementIsDownloadable`; all API tests pass.