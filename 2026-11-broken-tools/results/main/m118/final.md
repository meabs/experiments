I’ll trace the existing transactions endpoint, its validation/error conventions, and tests, then implement the date filters with focused coverage and run the mandated offline Maven test suite.

The existing endpoint already centralizes account visibility in `AccountService` and preserves descending date/id order via the repository. I’ll keep that access path and ordering intact, applying inclusive bounds after the same ordered query; invalid date syntax will be mapped to 400, and reversed bounds will use the existing invalid-input convention.

The focused API tests pass, including inclusive `from`/`to`, one-sided filters, malformed dates, and reversed ranges. The full suite has one pre-existing date-sensitive failure (`StatementPeriodsTest` expects September 2026 to be “last month,” while the environment date is November 2026); no transaction-related failures occur.

Implemented date filtering for `GET /api/accounts/{accountId}/transactions`.

Changes include:

- Optional inclusive `from` and `to` ISO date parameters.
- 400 responses for invalid dates or `from > to`.
- Existing ordering, response shape, access checks, and scope requirements preserved.
- Added API coverage for one-sided/range filters and invalid input.

Validation:

- `mvn -o -q -Dtest=AccountApiTest test` passes.
- Full `mvn -o -q test` has one pre-existing date-sensitive failure in `StatementPeriodsTest` unrelated to this change.