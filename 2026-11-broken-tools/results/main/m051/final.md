I’ll trace the existing transactions endpoint, its validation/error conventions, and tests, then implement the date filters and run the mandated offline test suite.

The endpoint currently delegates to one ordered repository query after the existing visibility check. I’ll preserve that access flow and ordering, add nullable `LocalDate` parameters, use date-bounded repository queries, and map conversion/type errors to the API’s standard 400 response.

The implementation compiles, and the full mandated run reached 27 tests but has one pre-existing failure in `StatementPeriodsTest` unrelated to this ticket. I’m running the account API tests separately and checking the diff now, including the invalid-date path.

Implemented inclusive `from`/`to` ISO date filtering for account transactions.

- Supports either or both query parameters.
- Invalid dates and reversed ranges return 400.
- Preserves ordering, response shape, access checks, and required scope.
- Existing account API tests: 10 passed.
- Full suite: 27 run, 1 unrelated pre-existing failure in `StatementPeriodsTest`.