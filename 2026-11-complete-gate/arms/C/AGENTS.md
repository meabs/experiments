# accounts-service

- Build and run the tests with `mvn -o -q test` (offline: every dependency is already in the local Maven repository).
  Do not run `mvn install`.
- README.md describes the security model and the API conventions.
- Before you say the tests pass, check how many tests ran and how many failed. Never disable, delete or weaken a
  test, or change test settings, to make a run pass. If a test fails for a reason unrelated to your change, leave it
  and say so in your summary.
- Before you finish, run `scripts/verify.sh`. It runs the full test suite and prints one line,
  `TESTS RUN n, FAILED f, ERRORS e, SKIPPED s`; it exits non-zero if no test ran or any test failed. Quote that line in
  your summary.
