I’ll trace the existing accounts endpoint and its validation conventions, implement the optional status filter, then run the mandated offline test suite and report the exact test counts.

The endpoint already centralizes visibility in `AccountService.listVisible()`. I’ll parse `status` at the controller boundary (so only exact `OPEN`/`CLOSED` are accepted), then filter that already-authorized list, preserving all access rules.

The implementation is in place and the first offline run passed all existing tests. I’m doing a final rerun after making the parameter name explicit, then I’ll verify the aggregate Surefire counts.

Implemented optional `status` filtering for `GET /api/accounts` in [AccountController.java](~/code/benchmark/brk-work/main/m034/ws/src/main/java/com/example/accounts/account/AccountController.java:39).

- Accepts exact `OPEN` or `CLOSED`.
- Invalid values return 400.
- Visibility rules remain unchanged; filtering occurs after authorization.
- No parameter preserves existing behavior.

Tests: 25 run, 0 failures, 0 errors, 0 skipped.