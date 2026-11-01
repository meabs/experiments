I’ll inspect the existing transaction endpoint, its tests, and the project conventions before implementing the date-range validation and filtering.

The endpoint currently delegates visibility checks to `AccountService` and uses a repository method that encodes descending date/id order. I’ll preserve that flow, add inclusive date predicates at the repository layer, and let Spring reject malformed ISO dates with HTTP 400 while treating an inverted range as an invalid request.

The implementation is in place. The normal offline test run completed successfully; I’m doing an additional focused API-test run to verify Spring’s query-parameter conversion and the derived repository queries at runtime.

Implemented transaction date filtering for `GET /api/accounts/{accountId}/transactions`.

- Added optional inclusive `from` and `to` ISO date parameters.
- Added validation for malformed dates and inverted ranges (`400`).
- Preserved ordering, response shape, authorization, visibility rules, and scope requirements.
- Added repository queries for each filtering combination.

Tests: standard Maven run passed 9 tests with 0 failures; focused account API run passed 10 tests with 0 failures.