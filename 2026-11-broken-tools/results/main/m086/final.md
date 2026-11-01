I’ll inspect the existing transaction endpoint, its validation conventions, and tests, then implement the date filters and run the offline Maven test suite.

The endpoint currently delegates visibility and ordering to `AccountService`/`TransactionRepository`. I’ll preserve that flow, add nullable `LocalDate` parameters, use inclusive repository predicates, and validate reversed ranges after visibility is checked.

The targeted account API tests pass. The full suite has one unrelated pre-existing failure: `StatementPeriodsTest` expects September 2026 to be downloadable, but the current date is November 2026; the transaction changes themselves compile and the account API tests remain green.

Implemented date filtering for `GET /api/accounts/{accountId}/transactions`:

- Added optional ISO `from` and `to` query parameters.
- Filters are inclusive and preserve existing ordering.
- Invalid dates and reversed ranges return 400.
- Existing access rules, scope requirements, and response fields remain unchanged.

Validation: `AccountApiTest` passes. The full suite has one unrelated pre-existing date-dependent failure in `StatementPeriodsTest` (expects September 2026 to be “last month” while the system date is November 2026).