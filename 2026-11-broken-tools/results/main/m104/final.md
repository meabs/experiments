I’ll inspect the existing controller, service, and tests to match the API’s current conventions, then implement the optional status filter and run the mandated offline Maven test suite.

The endpoint now parses `status` strictly via the existing `Account.Status` enum, filters only after `listVisible()` applies access rules, and relies on the established `IllegalArgumentException` → 400 handling for invalid values. I’m running the required offline test command next and will verify its test counts.

The offline suite completed successfully: 9 tests ran across the enabled test classes, with 0 failures, 0 errors, and 0 skipped. I made a small robustness tweak to name the query parameter explicitly, so I’m rerunning the same suite against the final diff.

Implemented optional status filtering for `GET /api/accounts` in [AccountController.java](~/code/benchmark/brk-work/main/m104/ws/src/main/java/com/example/accounts/account/AccountController.java).

- Supports exact `OPEN` and `CLOSED` values.
- Invalid values return 400.
- Access visibility is applied before filtering.
- No parameter preserves existing behavior.

Tests: 9 ran, 0 failures, 0 errors, 0 skipped.