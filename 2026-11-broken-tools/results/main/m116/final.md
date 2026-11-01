I’ll inspect the controller, service, and existing tests/conventions, then implement the optional status filter and run the required offline Maven test suite.

The implementation is in place: visibility is resolved exactly as before, then an optional exact `Account.Status` filter is applied. Invalid values flow through the existing 400 handler. I’m checking the focused account API tests separately because the full suite has an unrelated date-sensitive failure.

Implemented optional status filtering for `GET /api/accounts`.

- `status=OPEN` or `status=CLOSED` filters visible accounts.
- Missing status preserves existing behavior.
- Any other value returns 400 via the existing exception handler.
- Visibility rules remain unchanged.

Changed:
- [AccountController.java](~/code/benchmark/brk-work/main/m116/ws/src/main/java/com/example/accounts/account/AccountController.java:38)
- [AccountService.java](~/code/benchmark/brk-work/main/m116/ws/src/main/java/com/example/accounts/account/AccountService.java:66)

Testing:
- Focused `AccountApiTest`: 10 passed.
- Full suite: 27 run, 1 unrelated pre-existing failure in `StatementPeriodsTest` due its date-sensitive assertion.