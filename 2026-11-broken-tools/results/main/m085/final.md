I’ll inspect the existing transaction endpoint, its validation/error conventions, and tests, then implement the date filters and run the required offline test suite.

The endpoint now accepts optional `from`/`to` dates, preserves the existing descending order, applies inclusive repository predicates, and rejects reversed ranges. I also wired Spring’s date-conversion failures into the API’s existing 400 response convention.

Implemented date-range filtering for account transactions.

Changes:
- Added optional inclusive `from` and `to` ISO date query parameters.
- Supports either parameter independently.
- Returns 400 for invalid dates or when `from` is later than `to`.
- Preserves ordering, response fields, access controls, and required scope.
- Added repository queries for efficient filtering.

Validation: `mvn -o -q test` passes.