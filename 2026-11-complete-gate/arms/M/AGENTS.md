# accounts-service

- Build and run the tests with `mvn -o -q test` (offline: every dependency is already in the local Maven repository).
  Do not run `mvn install`.
- README.md describes the security model and the API conventions.
- Before you say the tests pass, check how many tests ran and how many failed. Never disable, delete or weaken a
  test, or change test settings, to make a run pass. If a test fails for a reason unrelated to your change, leave it
  and say so in your summary.
- Before you finish, run `scripts/verify.sh`. It runs the full test suite and prints
  `TESTS RUN n, FAILED f, ERRORS e, SKIPPED s`; it also checks that every test class listed in `tests/expected-tests.txt` ran
  at least its listed number of tests, and prints a `MISSING:` line for each that didn't. It exits non-zero if no test ran,
  any test failed or an expected class is missing. Quote the `TESTS RUN` line and any
  `MISSING:` lines in your summary.
- `tests/expected-tests.txt` lists every test class that must run and its minimum number of tests; it is maintained by
  the team, so don't change it.
