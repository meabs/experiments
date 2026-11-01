I’ll inspect the existing account-list endpoint, its validation conventions, and tests, then implement the optional status filter and run the required offline test suite.

The endpoint currently gets a role/tenant-filtered list from `AccountService`, and `Account.Status` already defines the only valid values. I’ll preserve that visibility path, add an exact case-sensitive parser at the controller boundary, and filter only after visibility has been established.

The implementation is in place and the existing suite passes. I’m adding focused API coverage for open/closed filtering and invalid case-sensitive values, then I’ll rerun the full suite and report the exact totals.

Implemented optional, case-sensitive `status` filtering for `GET /api/accounts`.

- Supports `OPEN` and `CLOSED`.
- Invalid values return 400.
- Visibility and unfiltered behavior remain unchanged.
- Added API tests for filtering and invalid input.

Tests: `27` run, `0` failures, `0` errors, `0` skipped via `mvn -o -q test`.