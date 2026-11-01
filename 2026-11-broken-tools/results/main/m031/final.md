I’ll inspect the existing account endpoint, security conventions, and tests, then implement the status filter and run the mandated offline test suite.

The endpoint already centralizes visibility in `AccountService.listVisible()`, so I’ll parse the optional value at the controller boundary (where invalid input becomes the API’s standard 400) and apply filtering only after visibility has been determined. This preserves tenant/role access behavior.

The implementation is in place. The first mandated test run is currently blocked by the local Maven cache failing to resolve Spring Boot 3.5.6 in offline mode (`Connection reset` while reading its cached descriptor); I’ll retry and inspect the diff for correctness.

The retry succeeded: `mvn -o -q test` passes. I also made the query parameter name explicit (`status`) so binding does not depend on compiler parameter metadata; the exact enum match still guarantees lowercase/unknown values are rejected as 400.

Implemented optional `status` filtering for `GET /api/accounts`.

- Supports exact `OPEN` and `CLOSED` values.
- Invalid values return 400.
- Visibility rules remain unchanged; filtering happens after access control.
- No status parameter preserves existing behavior.

Verified with `mvn -o -q test` — all tests pass.

[AccountController.java](~/code/benchmark/brk-work/main/m031/ws/src/main/java/com/example/accounts/account/AccountController.java:38)