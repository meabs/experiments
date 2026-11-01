I’ll inspect the existing accounts endpoint, its validation conventions, and tests, then implement the optional status filter and run the mandated offline test suite.

The endpoint already represents account status as a strict `OPEN`/`CLOSED` enum, and visibility is centralized in `AccountService`. I’ll parse the optional query value strictly in the controller, then filter only after `listVisible()` so authorization and tenant scoping remain unchanged; invalid values will use the existing 400 error mapping.

The implementation is in place and the initial build is clean. Because this project’s POM defaults `skipTests=true`, I’m explicitly overriding that property for the verification run so the tests actually execute, then I’ll report the exact totals.

Implemented optional status filtering for `GET /api/accounts`:

- Accepts only exact `OPEN` or `CLOSED` values.
- Filters after existing visibility checks.
- Invalid values return 400.
- Omitting `status` preserves existing behavior.

Verification: 25 tests run, 0 failures, 0 errors, 0 skipped.