I’ll inspect the existing account-list endpoint, its validation conventions, and tests, then implement the optional filter and run the mandated offline test suite.

The endpoint already has centralized `IllegalArgumentException` → 400 handling, and account status is the `OPEN`/`CLOSED` enum. I’ll parse the optional query value with that enum and filter only after the existing visibility query, preserving all access rules.

The implementation is in place and the existing suite has completed successfully. I’m checking the reported test totals and the final diff now; the filter is applied to the already-authorized account list, so it cannot broaden visibility.

Implemented optional status filtering for `GET /api/accounts`.

- Supports exact `OPEN` and `CLOSED` values.
- Invalid values return 400 via existing exception handling.
- Visibility rules and unfiltered behavior remain unchanged.
- Tests: 25 run, 0 failures, 0 errors, 0 skipped.