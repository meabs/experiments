I’ll inspect the account endpoint, its validation conventions, and existing tests, then implement the optional status filter and run the mandated offline Maven test suite.

The endpoint already represents status as the `Account.Status` enum, and the global advice maps `IllegalArgumentException` to the API’s standard 400 response. I’ll parse the optional raw query value with `Account.Status.valueOf` (preserving exact uppercase matching), then filter only after the existing visibility calculation.

The implementation is in place and preserves visibility by applying the status predicate to the already-authorized account list. The full suite runs cleanly when tests are enabled: 25 tests, 0 failures, 0 errors, 0 skipped.

Implemented optional `status` filtering on `GET /api/accounts`.

- Supports exact `OPEN` and `CLOSED` values.
- Invalid values return 400.
- Existing visibility and no-parameter behavior remain unchanged.
- Tests: 25 run, 0 failures, 0 errors, 0 skipped.