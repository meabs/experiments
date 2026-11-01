I’ll inspect the existing transaction endpoint, its tests, and the documented API conventions, then implement date filtering with validation and run the mandated offline test suite.

The endpoint now accepts optional ISO `from`/`to` dates, applies inclusive bounds while preserving descending date/id ordering, and rejects reversed ranges as 400. I’m checking compatibility details and the full test result before wrapping up.

Implemented date filtering for `GET /api/accounts/{accountId}/transactions`:

- Added optional inclusive `from` and `to` ISO date parameters.
- Supports either parameter independently.
- Rejects invalid dates and `from > to` with HTTP 400.
- Preserves ordering, response fields, authorization, and account visibility behavior.
- Existing unfiltered service method remains compatible.

`AccountApiTest` passes. The full suite has an unrelated pre-existing flaky failure in `BalanceAlertPublisherTest.alertReachesTheBroker`.