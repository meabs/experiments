# Working in this repository

- Build and run the tests with `mvn -o test` (offline: every dependency is already in the local Maven repository).
  Don't add -q: quiet mode prints nothing on success, so you can't see how many tests ran. Do not run `mvn install`.
- Before you say the tests pass, check how many tests ran and how many failed. Never disable, delete or weaken a
  test, or change test settings, to make a run pass. If a test fails for a reason unrelated to your change, leave it
  and say so in your summary.
- If the README, docs or comments disagree with the code, follow the code, and say what disagreed in your summary.
