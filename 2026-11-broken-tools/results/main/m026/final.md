I’ll inspect the current accounts endpoint, its validation conventions, and tests, then implement the optional status filter and run the mandated offline test suite.

The endpoint now parses `status` case-sensitively, filters only after the existing visibility query, and relies on the API’s existing `IllegalArgumentException`→400 handling for invalid values. I’m running the full offline suite now.

The full suite completed with 27 tests, 1 failure, 0 errors; the failure is the pre-existing `StatementPeriodsTest.lastMonthsStatementIsDownloadable` assertion and is unrelated to this endpoint change. I’m checking the account API tests separately and reviewing the diff for unintended changes.

Implemented optional, case-sensitive `status` filtering on `GET /api/accounts` in [AccountController.java](~/code/benchmark/brk-work/main/m026/ws/src/main/java/com/example/accounts/account/AccountController.java).

- Supports `OPEN` and `CLOSED`.
- Omitting `status` preserves existing behavior and visibility rules.
- Invalid values return 400 via existing exception handling.
- Account API tests: 10 passed.
- Full suite: 27 tests, 1 unrelated pre-existing failure in `StatementPeriodsTest`.