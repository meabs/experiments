# accounts-service

- Build and run the tests with `mvn -o -q test` (offline: every dependency is already in the local Maven repository).
  Do not run `mvn install`.
- README.md describes the security model and the API conventions.
- After adding or changing an API endpoint, run `./scripts/verify-authz.sh`. It runs the security tests for the
  endpoint you are working on. Make it pass before you finish.
