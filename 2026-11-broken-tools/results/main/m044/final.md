I’m inspecting the existing account-list endpoint, validation conventions, and tests first, then I’ll implement the smallest compatible change and run the mandated offline test suite.

The endpoint now parses `status` case-sensitively and filters only after the existing visibility calculation, so authorization scope and tenant behavior remain unchanged. I’ve also added coverage for both statuses and an invalid lowercase value; running the full offline suite now.

The new account API tests pass in isolation. The first full run exposed one mistaken expectation in my added test (the admin’s tenant has OPEN accounts 1–3, while account 4 belongs to another tenant); I corrected that. I’m rerunning the full suite to confirm the remaining result and distinguish any pre-existing failure.

Implemented optional, case-sensitive `status` filtering for `GET /api/accounts`.

- `OPEN` and `CLOSED` filter visible accounts.
- Missing `status` preserves existing behavior.
- Invalid values return `400`.
- Added API tests for filtering and validation.

`AccountApiTest` passes (12 tests). Full suite: 29 tests ran, with 1 pre-existing unrelated failure in `StatementPeriodsTest.lastMonthsStatementIsDownloadable`.