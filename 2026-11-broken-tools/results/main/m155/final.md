I’ll inspect the existing transaction endpoint, its tests, and the README conventions, then implement date-range filtering with validation and run the required offline test suite.

The endpoint now accepts optional `LocalDate` bounds, keeps the existing descending date/id ordering, and uses inclusive repository queries for each bound combination. I’m checking conversion/error behavior and running the full offline suite next.

The existing 13 tests pass. I’m doing a focused verification of the new cases (inclusive bounds, one-sided bounds, reversed bounds, and malformed dates) and will report the exact test count from Surefire.

Implemented date filtering for `GET /api/accounts/{accountId}/transactions`.

- Added optional ISO `from` and `to` query parameters.
- Bounds are inclusive and can be used independently.
- Reversed ranges return 400; invalid dates are rejected.
- Existing ordering, access rules, response shape, and scope requirements remain unchanged.

Validation: `25` tests run, `0` failures, `0` errors, `0` skipped via `mvn -o -q test`.