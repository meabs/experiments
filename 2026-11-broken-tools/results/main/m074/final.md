I’ll inspect the existing transaction endpoint, its tests, and the documented conventions, then implement date filtering with validation and run the required offline Maven tests.

The endpoint currently delegates ordering to a repository method and relies on the shared `IllegalArgumentException`→400 handler. I’ll preserve that flow, add inclusive repository bounds, and parse the optional strings after account visibility is checked so access semantics remain unchanged.

The implementation compiles and the full offline test suite passes. I’m doing one final review for strict `YYYY-MM-DD` handling and repository ordering before handing it over.

Implemented transaction date filtering for `GET /api/accounts/{accountId}/transactions`.

- Added optional inclusive `from` and `to` query parameters.
- Supports either parameter independently.
- Rejects malformed dates and reversed ranges with `400`.
- Preserves ordering, response shape, access checks, and required scope.
- Added repository queries for efficient date filtering.

Verified with:

```text
mvn -o -q test
```

All tests pass.