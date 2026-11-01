I’ll inspect the existing transaction endpoint and tests, then implement date-range parsing/validation in line with the project’s conventions and run the required offline test suite.

The endpoint currently delegates to a single descending transaction query. I’ll preserve that no-filter path, add inclusive repository queries for each boundary combination, and validate `from <= to` before querying. Spring’s date binding will enforce ISO date parsing and return 400 for malformed values.

The implementation is in place and the existing offline test suite passes. I’m doing a final diff review for API compatibility and repository query naming before handing it back.

Implemented date filtering for `GET /api/accounts/{accountId}/transactions`.

- Added optional inclusive `from` and `to` ISO date parameters.
- Added validation for malformed dates and `from > to` (400).
- Preserved ordering, response shape, authorization, and unfiltered behavior.
- Added repository queries for either or both boundaries.

Verified with `mvn -o -q test` (passes).