I’ll inspect the account endpoint, its validation conventions, and tests, then implement the optional status filter and run the required Maven and verification checks.

The existing API already represents account status as a strict `OPEN`/`CLOSED` enum, and the global handler maps `IllegalArgumentException` to the project’s 400 response. I’ll parse the optional query value explicitly and filter only after `listVisible()`, preserving all existing access rules.

The implementation is in place and the offline Maven test run completed without a reported failure. I’m running the repository’s required `scripts/verify.sh` now and will report its exact test summary.

Implemented optional status filtering for `GET /api/accounts`:

- Accepts only exact `OPEN` or `CLOSED`.
- Filters after visibility checks, preserving access behavior.
- Invalid values return 400.
- No parameter preserves existing behavior.

Verification: `TESTS RUN 25, FAILED 0, ERRORS 0, SKIPPED 0`