I’ll inspect the existing transactions endpoint, its tests, and the project conventions, then implement the date filters and run the mandated offline test suite.

The endpoint now accepts optional ISO `from`/`to` dates, validates their ordering, and uses inclusive repository bounds while preserving visibility and sorting. I’m running the project’s required offline tests now.

Implemented date filtering for `GET /api/accounts/{accountId}/transactions`:

- Added optional inclusive `from` and `to` ISO date parameters.
- Added validation for malformed dates and `from > to` (400).
- Preserved ordering, response fields, authorization, visibility, and no-filter behavior.
- Added repository queries for efficient bounded filtering.

`mvn -o -q test` could not run because Maven failed to resolve the Spring Boot dependency descriptor offline (`Connection reset`).