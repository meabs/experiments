I’ll inspect the existing account endpoint, domain model, and tests, then add the query filter following the project’s current validation/error conventions. I’ll run the required Maven tests and `scripts/verify.sh` before summarizing.

The endpoint currently gets all visible accounts from `AccountService`, with visibility enforced by role/tenant before serialization. I’ll preserve that flow and apply the status predicate only after visibility is determined; parsing will use the existing enum so anything other than exact `OPEN`/`CLOSED` becomes a 400.

The implementation is in place: visibility is computed exactly as before, then an optional enum status filter is applied. The first offline Maven invocation hit a transient dependency-resolution reset; the retry launched the suite successfully, and I’m checking its recorded results before running the required verification script.

I made one compatibility refinement: requests without `status` still call the original no-argument service method, so existing callers/mocks observe the same path. I’m rerunning the suite and final verification against this version.

Implemented optional `status` filtering for `GET /api/accounts`.

- Accepts exact `OPEN` or `CLOSED`; invalid values return 400.
- Applies filtering after existing visibility checks.
- Preserves behavior when `status` is omitted.

Verification passed:

`TESTS RUN 25, FAILED 0, ERRORS 0, SKIPPED 0`