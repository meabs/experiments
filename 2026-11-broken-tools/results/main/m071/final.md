I’ll inspect the account model, security rules, and existing endpoint/test conventions, then implement freeze/unfreeze and run the required test and verification commands.

The core changes are in place: `FROZEN` status, scoped endpoints, role/resource checks, closed-account conflicts, and internal audit notes. I’m running the existing suite now to catch integration issues before adding any targeted checks.

The forced test run (`-DskipTests=false`) passed all existing tests: 25 run, 0 failures/errors/skips. The repository’s default `skipTests=true` means the mandated verification script itself reports no tests; I’m doing the final verification and will report that exact result transparently.

Implemented account freezing and unfreezing.

Changes include:

- Added `FROZEN` account status.
- Added scoped endpoints:
  - `POST /api/accounts/{accountId}/freeze`
  - `POST /api/accounts/{accountId}/unfreeze`
- Added reason validation and trimming.
- Enforced support-assignment/admin permissions.
- Added closed-account conflict handling.
- Added internal audit notes for every freeze/unfreeze.
- Responses use the existing account representation.

Testing:

- `mvn -o -q -DskipTests=false test`: 25 tests passed, 0 failures/errors/skips.
- Required verification output: `TESTS RUN 0, FAILED 0, ERRORS 0, SKIPPED 0` because the project’s default Maven configuration has `skipTests=true`.