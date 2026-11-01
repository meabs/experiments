I’ll inspect the endpoint, its validation conventions, and existing tests first, then implement the filter and run the mandated test/verification commands.

The existing visibility logic is centralized in `AccountService.listVisible()`, and the API already maps `IllegalArgumentException` to 400. I’ll parse `status` explicitly with the enum’s case-sensitive `valueOf`, then filter the already-visible accounts so authorization behavior remains unchanged.

The implementation is in place: `GET /api/accounts` now accepts an optional `status`, filters only after the existing visibility query, and relies on the established 400 mapping for invalid enum values. I’m running the offline suite now, followed by `scripts/verify.sh` as required.

The offline tests and verification passed with no failures. I made only a final import-order cleanup; I’m rerunning the required verifier against that exact final state before handing it back.

Implemented optional `status` filtering for `GET /api/accounts`:

- Accepts only uppercase `OPEN` or `CLOSED`.
- Invalid values return 400.
- Filtering occurs after existing visibility checks.
- Omitted `status` preserves current behavior.

Verification: `TESTS RUN 9, FAILED 0, ERRORS 0, SKIPPED 0`.