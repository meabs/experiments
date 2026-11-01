I’ll inspect the account endpoint, its validation conventions, and existing tests, then implement the optional status filter and run the mandated offline Maven test suite.

The endpoint currently obtains visibility-filtered accounts from `AccountService`, while `ApiExceptionHandler` already maps `IllegalArgumentException` to 400. I’ll parse the optional value strictly with the existing `Account.Status` enum, then filter only after visibility is established.

The implementation is in place, including an explicit query-parameter name so it does not depend on compiler parameter metadata. The offline test suite passes; I’m doing one targeted API test run as an additional check because the repository’s default Surefire configuration excludes the account API test class.

Implemented optional status filtering for `GET /api/accounts`:

- Accepts exactly `OPEN` or `CLOSED`.
- Filters only after applying existing visibility rules.
- Invalid values return 400 via existing exception handling.
- Omitting `status` preserves current behavior.

Verified with:

- `mvn -o -q test`
- `mvn -o -q -Dtest=AccountApiTest test`