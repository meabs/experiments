I’ll inspect the existing transactions endpoint, its tests, and the README conventions first, then implement the date filtering with validation and run the prescribed offline test suite.

The endpoint currently delegates visibility to `AccountService` before loading transactions, and the repository already guarantees descending date/id order. I’ll preserve that flow, add inclusive range-specific repository queries, and validate `from <= to` after visibility is checked so access behavior remains unchanged.

The targeted account API tests pass, including inclusive range filtering, reversed ranges, and malformed dates. I’m running the complete mandated suite now; one pre-existing date-dependent unit test may be sensitive to the current system date, so I’ll distinguish that from any regression.

Implemented transaction date filtering:

- Added optional inclusive `from`/`to` ISO date query parameters.
- Supports either parameter independently.
- Rejects malformed dates and reversed ranges with `400`.
- Preserves visibility, scope checks, response shape, and descending order.
- Added API tests for filtering and validation.

`AccountApiTest` passes. Full `mvn -o -q test` has one pre-existing failure in `StatementPeriodsTest` due its system-date-sensitive expectation (`2026-09` vs current `2026-11`).