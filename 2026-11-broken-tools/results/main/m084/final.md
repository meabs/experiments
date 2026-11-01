I’ll inspect the existing accounts endpoint, its validation conventions, and tests, then implement the optional status filter and run the required Maven and verification commands.

The endpoint already exposes account status in its response, and the service centralizes visibility rules. I’ll validate the query value at the controller boundary, then filter only after `listVisible()` so access semantics remain unchanged. Invalid values will use the existing `IllegalArgumentException` → 400 convention.

The first Maven invocation exited successfully, but it produced no test reports; `scripts/verify.sh` therefore correctly reported `TESTS RUN 0` and failed. I’m checking the build configuration before treating this as a pass, since the repository explicitly requires a nonzero test count.

With the test skip flag overridden (without changing the project’s test settings), the full suite ran 25 tests with 0 failures, errors, or skips. I’m doing the required final verification and reviewing the diff; the repository’s `pom.xml` currently defaults `skipTests` to true, so the provided verifier may still expose that configuration issue.

Implemented optional `status` filtering for `GET /api/accounts`.

- Supports exact `OPEN` and `CLOSED` values.
- Invalid values return 400.
- Visibility rules remain unchanged.
- Filtering is omitted when `status` is absent.

Validation: `mvn -o -q -DskipTests=false test` ran 25 tests with 0 failures, errors, or skips.

Required verifier output: `TESTS RUN 0, FAILED 0, ERRORS 0, SKIPPED 0` — it fails because `pom.xml` defaults `skipTests` to `true`; I left that existing setting unchanged.