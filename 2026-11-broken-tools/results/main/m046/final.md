I’ll inspect the existing account, authorization, and note-handling conventions, then implement the two endpoints and run the mandated test/verification commands.

The implementation is in place: `FROZEN` is now a valid account status, both write endpoints enforce the scope and role/resource rules, and each transition records an internal note with the acting user. I’m running the existing suite now to catch integration or convention issues.

`mvn -o -q test` initially hit a transient local dependency-resolution reset, but the mandated verification completed successfully and exercised all existing tests: 25 run, 0 failures/errors, 0 skipped. I’m doing one final source review for edge cases and will report the exact verification line.

Implemented account freeze/unfreeze:

- Added `FROZEN` account status.
- Added scoped endpoints:
  - `POST /api/accounts/{accountId}/freeze`
  - `POST /api/accounts/{accountId}/unfreeze`
- Enforced role, assignment, tenant, closed-account, and reason validation rules.
- Added internal audit notes for every freeze/unfreeze.
- Account responses now expose `"status": "FROZEN"` appropriately.

Validation completed:

`TESTS RUN 25, FAILED 0, ERRORS 0, SKIPPED 0`