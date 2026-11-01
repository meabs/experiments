I’ll inspect the existing accounts endpoint, its validation/error conventions, and tests, then implement the optional status filter and run the mandated test/verification commands.

The endpoint now accepts an optional exact-case status string, filters only after the existing visibility logic, and relies on the API’s existing `IllegalArgumentException`→400 mapping for invalid values. I also added coverage for both statuses and invalid casing/values.

Implemented optional status filtering for `GET /api/accounts`:

- Supports exact `OPEN` and `CLOSED` values.
- Omitting `status` preserves existing behavior and visibility rules.
- Invalid values return `400 Bad Request`.
- Added API tests for filtering and validation.

Verification passed:

`TESTS RUN 27, FAILED 0, ERRORS 0, SKIPPED 0`