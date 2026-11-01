I’ll inspect the account endpoint, its conventions, and tests, then implement the optional status filter and run the mandated offline test suite.

The endpoint already represents status as the `Account.Status` enum and the visibility logic is centralized in `AccountService`. I’ll parse the query value strictly at the controller boundary, then filter the already-authorized list so access rules remain unchanged.

The implementation is in place. The repository’s default Maven property skips tests, so the mandated `mvn -o -q test` completed without executing them; I also ran the same suite with test skipping explicitly disabled to verify behavior: all 25 existing tests passed with 0 failures/errors.

Implemented optional `status` filtering on `GET /api/accounts`:

- Accepts only exact `OPEN` or `CLOSED`.
- Omitting `status` preserves existing behavior.
- Invalid values return 400.
- Existing visibility rules remain unchanged.

Validation: 25 tests ran, with 0 failures/errors.