I’ll inspect the account API, its tests, and the README conventions, then implement the optional status filter and run the offline test suite.

The filter is now applied after the existing visibility rules, so authorization scope and tenant behavior stay unchanged. Invalid or lowercase values are parsed strictly and become 400 responses; I’m checking the full test result and diff now.

All tests pass with the repository’s required offline command; I also ran them with `-DskipTests=false` to ensure the test classes actually executed. The final diff is limited to the controller parameter and service-level post-visibility filtering.

Implemented optional `status` filtering for `GET /api/accounts`.

- Accepts only `OPEN` or `CLOSED` in uppercase.
- Invalid values return 400.
- Filtering occurs after existing visibility checks.
- Existing behavior is unchanged when omitted.

Tests pass with `mvn -o -q test` and full execution via `mvn -o -q -DskipTests=false test`.