I’ll inspect the account endpoint, its validation conventions, and existing tests, then implement the optional status filter and run the mandated offline Maven test suite.

The endpoint currently obtains a visibility-filtered list from `AccountService`, and account status is already represented by an `OPEN`/`CLOSED` enum. I’ll parse the optional query value strictly, apply the status filter after the existing visibility rules, and cover open/closed, omitted, and invalid cases.

The implementation and focused API tests are in place. The offline Maven suite is running now; I’m checking the result and will adjust if Spring’s argument/error handling exposes any edge case.

The implementation compiles and the full test suite passes with tests explicitly enabled (`-DskipTests=false`); the repository’s default `mvn -o -q test` also completes successfully. I corrected the focused test to reflect that ADA’s tenant has three open accounts and one closed account.

Implemented optional `status=OPEN|CLOSED` filtering for `GET /api/accounts`.

- Invalid or lowercase values return 400.
- Existing visibility rules and no-parameter behavior remain unchanged.
- Added API tests for filtering and invalid input.

Tests pass with `mvn -o -q test` and the account API tests explicitly enabled.