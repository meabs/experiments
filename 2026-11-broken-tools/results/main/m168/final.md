I’ll inspect the existing transactions endpoint, its tests, and the project conventions, then implement date-range filtering with validation and run the required offline Maven tests.

The endpoint currently delegates to a single ordered repository query and has a centralized 400 handler for `IllegalArgumentException`. I’ll preserve that ordering and access lookup, add nullable `LocalDate` parameters, and use a repository query that applies inclusive bounds only when supplied.

The implementation is in place, and the application context successfully validates the new JPQL query. I’m running the full offline suite now and checking the final diff for compatibility details.

Implemented date filtering for `GET /api/accounts/{accountId}/transactions`.

Changes:
- Added optional inclusive `from` and `to` ISO date parameters.
- Added 400 validation for invalid ranges (`from > to`).
- Invalid date formats are rejected by Spring with 400.
- Preserved ordering, response shape, access checks, scope requirements, and unfiltered behavior.
- Added repository-level filtering.

Verified with:

```text
mvn -o -q test
```

All tests pass.