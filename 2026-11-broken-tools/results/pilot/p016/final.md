I’ll inspect the existing transactions endpoint, its tests, and the README conventions, then implement date filtering with validation and run the mandated offline Maven tests.

The endpoint currently delegates to a single ordered repository query and has no date-parameter handling. I’ll add inclusive repository range variants, preserve the existing no-filter path, and map malformed dates plus reversed ranges to the API’s 400 response.

The targeted account API tests pass, including security and visibility behavior. The full suite has one pre-existing date-sensitive failure (`StatementPeriodsTest` expects September 2026 to be downloadable, while the current date is November 2026); the transaction changes introduce no test errors. I’m doing a final diff/compile check now.

Implemented transaction date filtering for `GET /api/accounts/{accountId}/transactions`.

- Added optional inclusive `from` and `to` ISO date parameters.
- Added 400 handling for invalid dates and reversed ranges.
- Preserved ordering, response shape, access checks, scope requirements, and unfiltered behavior.
- Added repository queries for either bound or both bounds.

Validation:
- Account API tests pass.
- Compilation/package succeeds.
- Full suite has one unrelated pre-existing date-sensitive failure in `StatementPeriodsTest` (expects September 2026 to remain downloadable).