I’ll inspect the account endpoint, its existing validation conventions, and tests, then implement the optional filter and run the mandated offline Maven test suite with the test counts.

The endpoint now parses `status` strictly as `OPEN` or `CLOSED`, filters only after the existing visibility service result, and relies on the established `IllegalArgumentException` → 400 handling. I’m running the required offline test command now and will report its actual test totals.

The mandated suite completed successfully: 9 tests ran (4 admin-customer, 5 closure), with 0 failures, 0 errors, and 0 skipped. The repository’s Maven configuration excludes the account API test class, so I’m also checking that existing excluded API tests can be run explicitly without changing project test settings.

Implemented optional status filtering for `GET /api/accounts`.

- Accepts exactly `OPEN` or `CLOSED`.
- Invalid values return 400.
- No status preserves existing behavior and visibility rules.
- Filtering occurs after access-controlled account selection.

Tests:
- Required suite: 9 passed, 0 failed.
- Explicit `AccountApiTest`: 10 passed, 0 failed.