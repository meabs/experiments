I’ll inspect the existing accounts endpoint, its security/API conventions, and tests, then implement the optional status filter and run the mandated offline test suite.

The current visibility logic is centralized in `AccountService.listVisible()`, while `Account.Status` already exposes the exact `OPEN`/`CLOSED` enum values. I’ll validate the optional query value through that enum and apply filtering after the existing visibility rules, so access semantics stay unchanged.

The implementation is in place. The full mandated suite reached the code successfully, but it has one pre-existing date-sensitive failure: it expects September 2026 to be “last month,” while the environment date is November 2026. I’m running the account API tests separately and checking the diff for regressions.

Implemented optional `status` filtering for `GET /api/accounts`.

- Accepts exactly `OPEN` or `CLOSED`.
- Invalid values return `400`.
- Filtering occurs after existing visibility rules.
- Requests without `status` preserve existing behavior.

`AccountApiTest` passes (10 tests). The full suite has one unrelated pre-existing date-sensitive failure in `StatementPeriodsTest`.