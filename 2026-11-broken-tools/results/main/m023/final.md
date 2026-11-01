I’ll trace the existing account-list endpoint and its validation conventions, implement the optional status filter without changing visibility rules, then run the mandated offline tests and `scripts/verify.sh`.

The endpoint currently gets a visibility-filtered list from `AccountService`; I’ll preserve that call and apply status filtering afterward, so tenant/role visibility remains unchanged. Invalid or lower-case values will be rejected through the existing 400 exception convention.

The implementation compiles, but the existing suite has one unrelated failure in `StatementPeriodsTest` (27 run, 1 failed, 0 errors); I’m checking the new endpoint behavior separately, then I’ll run the required verification script and report that baseline failure accurately.

Implemented optional `status` filtering for `GET /api/accounts` in [AccountController.java](~/code/benchmark/brk-work/main/m023/ws/src/main/java/com/example/accounts/account/AccountController.java:39).

- Supports exact `OPEN` and `CLOSED` values.
- Omitting `status` preserves existing behavior and visibility rules.
- Invalid values return 400 via the existing exception handler.
- `AccountApiTest`: 10 passed.

Full verification is blocked by an unrelated pre-existing date-sensitive test failure:

`TESTS RUN 27, FAILED 1, ERRORS 0, SKIPPED 0`