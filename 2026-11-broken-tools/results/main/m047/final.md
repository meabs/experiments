I’ll inspect the existing accounts endpoint, its validation/error conventions, and tests, then implement the optional status filter and run the required verification commands.

The endpoint now parses the optional status case-sensitively, filters only after the existing visibility service result, and lets invalid values use the API’s established 400 handling. I’m running the full verification script now.

Implemented optional `status` filtering on `GET /api/accounts`.

- Supports exact `OPEN` and `CLOSED` values.
- Invalid values return 400.
- Visibility and default unfiltered behavior remain unchanged.
- Filtering occurs after authorization visibility checks.

Verification:

`TESTS RUN 9, FAILED 0, ERRORS 0, SKIPPED 0`