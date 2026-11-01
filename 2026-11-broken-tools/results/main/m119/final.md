I’ll inspect the existing account endpoint, its validation conventions, and tests, then implement the optional status filter and run the mandated offline Maven test suite.

The endpoint currently has no query binding, while the project’s exception advice already maps `IllegalArgumentException` to the API’s 400 response. I’ll parse the parameter explicitly (preserving case sensitivity), filter only after the existing visibility rules, and leave the no-parameter path unchanged.

The implementation and focused API tests are in place. I’m running the repository-mandated offline test command now, then I’ll verify the exact test totals and inspect the diff for unintended behavior changes.

The code diff is clean and preserves the existing no-argument service method. The mandated test run is currently blocked before compilation by Maven dependency resolution (`spring-boot-starter-web:3.5.6` reports “Connection reset” in offline mode); I’m retrying once and will report the actual test count if the suite starts.

The suite now runs: 28 tests, with one failure in the new test caused by my expectation (the acme admin cannot see globex account 4; their four accounts are 1, 2, 3, and closed 5). I’m correcting that test expectation and rerunning.

The corrected suite passes: 28 tests total, 0 failures, 0 errors, 0 skipped. I’m doing one final diff/status check; the status filter is case-sensitive, invalid values use the existing 400 handling, and visibility is applied before filtering.

Implemented optional status filtering for `GET /api/accounts`.

- Supports exact `OPEN` and `CLOSED` values.
- Invalid values return 400.
- Existing visibility rules and no-parameter behavior are preserved.
- Added API coverage for filtering, visibility, and invalid input.

Tests: `mvn -o -q test` — 28 run, 0 failures, 0 errors, 0 skipped.