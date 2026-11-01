I’ll inspect the API/controller, domain model, and existing tests to add the optional status filter consistently, then run the required Maven and verification commands.

The existing endpoint applies visibility in `AccountService.listVisible()`, while `Account.Status` already has the exact `OPEN`/`CLOSED` values. I’ll preserve the no-argument service behavior and add an optional raw query parameter that is parsed case-sensitively, so invalid values map to the API’s existing 400 handling.

The implementation compiles and the API tests can be checked independently. The full Maven run currently reports one pre-existing failure in `StatementPeriodsTest` (27 run, 1 failed, 0 errors, 0 skipped), unrelated to this endpoint change; I’ll preserve it and run the focused account tests plus the required verification script.

Implemented optional status filtering for `GET /api/accounts`.

- Supports exact `OPEN` and `CLOSED` values.
- Omitting `status` preserves existing behavior and visibility rules.
- Invalid values return 400.
- Filtering occurs after account visibility is determined.

Validation:

- Account API tests: 10 passed.
- Required verification: `TESTS RUN 27, FAILED 1, ERRORS 0, SKIPPED 0`
- The single failure is the pre-existing unrelated `StatementPeriodsTest.lastMonthsStatementIsDownloadable` failure.