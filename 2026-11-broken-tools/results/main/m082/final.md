I’ll inspect the existing accounts endpoint, security conventions, and tests, then implement the optional status filter and run the mandated offline Maven test suite.

The visibility logic is centralized in `AccountService.listVisible()`, so I’ll validate the query value at the controller boundary and filter only after that visibility result. This preserves tenant/role access exactly while letting the existing `IllegalArgumentException` → 400 handler cover invalid values.

The implementation is in place. The full mandated suite reached the application tests, but one pre-existing `StatementPeriodsTest` failed because its date assertion is time-sensitive; I’m checking the account API tests separately and reviewing the build configuration to ensure the new request parameter binds reliably.

The targeted `AccountApiTest` passes, and the diff is limited to `AccountController`. Invalid values (including lowercase or empty strings) throw `IllegalArgumentException`, which the existing API advice maps to 400; omitted `status` still returns the unchanged visible list.

Implemented optional `status` filtering for `GET /api/accounts` in [AccountController.java](~/code/benchmark/brk-work/main/m082/ws/src/main/java/com/example/accounts/account/AccountController.java:39).

- Supports exact `OPEN` and `CLOSED` values.
- Invalid values return 400.
- Existing visibility and unfiltered behavior are preserved.
- `AccountApiTest` passes.

The full suite has one unrelated pre-existing date-sensitive failure in `StatementPeriodsTest`.