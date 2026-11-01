I’ll inspect the controller, service, and tests first, then implement the smallest change that preserves the existing visibility rules and run the prescribed offline Maven tests.

The existing list method already applies all tenant/role visibility rules in `AccountService`. I’ll parse `status` at the controller boundary (case-sensitive via the existing `Account.Status` enum), then filter only after visibility has been computed, so the security behavior remains unchanged and invalid values map to the API’s standard 400 response.

The implementation is in place and the full prescribed offline test command passes. I’m doing one targeted API test run as a final check of the existing account endpoint path after adding the query parameter.

Implemented optional `status` filtering for `GET /api/accounts`.

- Accepts only exact `OPEN` or `CLOSED` values.
- Invalid values return 400.
- Filtering occurs after existing visibility checks, preserving security behavior.
- No status parameter keeps existing behavior.

Tests passed:

- `mvn -o -q test`
- Targeted `AccountApiTest` (10 tests)