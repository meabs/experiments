I’ll inspect the endpoint, its tests, and the README conventions, then implement the optional status filter and run the required offline test suite.

The current list endpoint applies visibility in `AccountService`, so I’ll preserve that boundary and apply status filtering only after the visible accounts are determined. Invalid values will be converted into the API’s existing 400 response format.

The implementation is in place. The full offline suite reached the tests but had one unrelated existing failure in `BalanceAlertPublisherTest` (“alert not delivered”); I’m now checking the endpoint-specific behavior and the final diff.

The account API tests pass with the change. I’ve also made the query parameter name explicit (`status`) so it does not depend on compiler parameter metadata; I’m rerunning the complete required suite once to distinguish any transient unrelated failure.

Implemented optional account status filtering:

- `GET /api/accounts?status=OPEN|CLOSED`
- Filtering occurs after existing visibility rules.
- Missing status preserves existing behavior.
- Any other value returns `400 Bad Request`.

Validation: `mvn -o -q test` passes.