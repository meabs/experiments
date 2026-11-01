I’ll inspect the existing transaction endpoint, its tests, and the README conventions first, then implement the date filtering with validation and run the required offline Maven test suite.

The existing endpoint gets transactions through `AccountService` and a repository method that already enforces descending date/id order. I’ll preserve that access path and add date-aware repository queries, while parsing the optional query values explicitly so malformed dates and reversed ranges consistently map to the API’s existing 400 response.

Implemented date-range filtering for `GET /api/accounts/{accountId}/transactions`.

- Added optional inclusive `from` and `to` ISO date parameters.
- Invalid dates and reversed ranges return 400.
- Preserved ordering, response fields, access rules, and scope requirements.
- Added repository queries for either or both bounds.

Validation: `mvn -o -q test` passed — 25 tests run, 0 failures, 0 errors.