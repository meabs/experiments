I’ll inspect the endpoint, its request/validation conventions, and existing tests, then implement the optional status filter and run the mandated offline test suite.

The list endpoint currently obtains the caller-visible accounts in `AccountService`, so I’ll parse `status` at the controller boundary (case-sensitive via `Account.Status.valueOf`) and filter only after visibility is computed. Invalid values will flow through the existing `IllegalArgumentException` → 400 convention.

The implementation compiles and the API tests ran, but the full suite has one unrelated existing failure in `StatementPeriodsTest` (a date-dependent assertion), not in account endpoint tests. I’m checking the exact failure context and will add focused coverage for OPEN/CLOSED, invalid case, and visibility preservation.

Focused `AccountApiTest` now passes with the new cases. The repository-wide command remains blocked only by the pre-existing `StatementPeriodsTest` date assertion (`2026-09` is no longer UTC last month on the current date); no account API tests fail. I’m doing a final diff/status check.

Implemented optional, case-sensitive `status` filtering for `GET /api/accounts` in [AccountController.java](~/code/benchmark/brk-work/pilot/p017/ws/src/main/java/com/example/accounts/account/AccountController.java:38). Invalid values return 400 through the existing exception convention, while visibility rules remain unchanged.

Added API coverage for filtering, visibility, and case sensitivity in [AccountApiTest.java](~/code/benchmark/brk-work/pilot/p017/ws/src/test/java/com/example/accounts/AccountApiTest.java:51).

`AccountApiTest` passes. The full `mvn -o -q test` run has one unrelated pre-existing date-based failure in `StatementPeriodsTest`.