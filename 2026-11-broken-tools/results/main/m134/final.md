I’ll inspect the existing accounts endpoint, its conventions, and tests, then implement the optional status filter and run the required verification.

The existing list first applies visibility in `AccountService`; I’ll preserve that and apply status filtering afterward in the controller. Invalid values will use the project’s existing `IllegalArgumentException` → 400 convention.

The implementation is in place, with coverage for a valid `CLOSED` filter, visibility preservation, and lowercase rejection. I’m running the full offline suite and the required verification script now.

Implemented optional status filtering for `GET /api/accounts`.

- Supports `status=OPEN` and `status=CLOSED`.
- Invalid or lowercase values return 400.
- Visibility rules remain unchanged; filtering occurs after authorization.
- Added API tests covering filtering and validation.

Verification: `TESTS RUN 27, FAILED 0, ERRORS 0, SKIPPED 0` (verify OK).