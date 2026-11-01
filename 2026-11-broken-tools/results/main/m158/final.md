I’ll inspect the account listing endpoint and its tests, implement the optional status filter with strict validation, then run the required Maven tests and `scripts/verify.sh`.

The endpoint currently delegates visibility entirely to `AccountService.listVisible()`. I’ll preserve that authorization path and apply the status filter only after visibility is established, with exact enum parsing so malformed or lowercase values become 400.

The code compiles, but the initial Maven invocation reported no visible test output, and `scripts/verify.sh` confirms `TESTS RUN 0`. I’m checking the project’s test configuration before treating this as a valid pass, since the repository instructions require a nonzero test count.

The repository’s `pom.xml` has a pre-existing `<skipTests>true</skipTests>`, so the prescribed commands otherwise run zero tests. I’m leaving that test setting untouched and running the suite with the explicit `-DskipTests=false` override to validate the change; the implementation itself is confined to the controller.

The explicit test run completed successfully: 25 tests ran with 0 failures, 0 errors, and 0 skipped. The required verification script still reports its pre-existing zero-test condition because it does not override the POM’s `skipTests` flag.

Implemented optional `status` filtering on `GET /api/accounts`.

- Accepts only `OPEN` or `CLOSED` (case-sensitive).
- Invalid values return 400.
- Visibility rules and unfiltered behavior remain unchanged.

Validation: `mvn -o -q test -DskipTests=false` — 25 tests, 0 failures/errors/skips.

Required verification output: `TESTS RUN 0, FAILED 0, ERRORS 0, SKIPPED 0` (pre-existing `skipTests=true` in `pom.xml`).