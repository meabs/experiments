I’ll inspect the endpoint, its tests, and the project conventions, then implement the optional status filter and run the mandated offline test suite.

The endpoint now accepts an optional enum-valued `status` parameter and applies it after the existing visibility calculation, so authorization and tenant scoping remain unchanged. The existing offline test suite is passing; I’m doing a final diff check and targeted validation of invalid values.

Implemented optional `status` filtering on `GET /api/accounts`.

- Accepts exactly `OPEN` or `CLOSED`.
- Invalid values return `400`.
- Omitting `status` preserves existing behavior.
- Filtering occurs after existing visibility checks.

Verified with `mvn -o -q test` and `git diff --check`.