I’ll inspect the existing transaction endpoint, its tests, and the documented API conventions, then implement date filtering with validation and run the prescribed offline Maven tests.

The endpoint currently delegates ordering to a repository method and performs account visibility checks in the service. I’ll preserve that flow, add inclusive repository variants for each boundary combination, and let Spring parse ISO `LocalDate` query values while rejecting reversed ranges as a 400.

Implemented inclusive transaction date filtering:

- Added optional `from` and `to` ISO date query parameters.
- Supports either parameter independently.
- Rejects invalid dates and ranges where `from > to` with HTTP 400.
- Preserves ordering, response shape, access checks, and required scope.
- Existing behavior remains unchanged without filters.

Validation: `mvn -o -q test` passes.