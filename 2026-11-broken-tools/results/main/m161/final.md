I’ll inspect the existing transaction endpoint, its validation/error conventions, and tests, then implement date filtering and run the required offline test suite.

The endpoint now accepts optional `LocalDate` bounds, validates their ordering, and uses date-range repository queries that preserve the existing descending date/id order. I’m checking conversion/error behavior and then will run the full suite.

The first full test run completed with 27 tests: 1 pre-existing failure in `StatementPeriodsTest.lastMonthsStatementIsDownloadable`, unrelated to this change; the rest passed. I made the date format explicit as ISO and am doing a final compile/test verification.

Implemented transaction date filtering:

- Added optional ISO `from` and `to` query parameters.
- Supports inclusive lower/upper bounds independently.
- Rejects invalid dates and `from > to` with HTTP 400.
- Preserves ordering, response shape, access rules, and required scope.
- Added repository queries for filtered ranges.

Verification: `mvn -o -q test` ran 27 tests; 26 passed and 1 unrelated existing test failed (`StatementPeriodsTest.lastMonthsStatementIsDownloadable`).