I’ll inspect the controller/service and existing tests, add the optional validated status filter without changing authorization behavior, then run the required Maven tests and `scripts/verify.sh`.

The endpoint now parses `status` strictly via the existing `Account.Status` enum, applies filtering after the existing visibility rules, and retains the no-parameter service behavior. I’ve also added API coverage for both statuses and invalid casing/values.

The first test run exposed an error in the newly added expectation (I had included an account from another tenant), not in the implementation; I corrected that fixture expectation. The full Maven test command now exits successfully, and I’m running the mandated verification script for the authoritative test count.

Implemented optional status filtering for `GET /api/accounts`.

- Supports exact `OPEN` and `CLOSED` values.
- Invalid values return `400`.
- Existing visibility and no-parameter behavior remain unchanged.
- Added API tests for filtering and validation.

Verification:

`TESTS RUN 27, FAILED 0, ERRORS 0, SKIPPED 0`  
`verify: OK`