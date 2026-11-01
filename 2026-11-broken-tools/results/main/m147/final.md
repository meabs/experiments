I’ll inspect the controller, domain model, and existing request-validation conventions, then implement the optional filter and run the mandated offline Maven tests.

The existing visibility logic is centralized in `AccountService.listVisible()`, so I’ll preserve it unchanged and apply status filtering only to that already-authorized result. Invalid values will use the API’s existing `IllegalArgumentException`→400 handling.

Implemented optional status filtering for `GET /api/accounts`:

- `?status=OPEN` or `?status=CLOSED` filters the already-authorized account list.
- Omitting `status` preserves existing behavior.
- Any other value returns `400 Bad Request`.
- Account visibility rules remain unchanged.

Verified with `mvn -o -q test` — all tests pass.