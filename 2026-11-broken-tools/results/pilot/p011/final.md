I’ll inspect the existing account, authorization, and note-handling conventions, then implement the two endpoints and run the offline Maven tests.

The freeze/unfreeze flow is implemented with scope checks, resource-level role checks, closed-account conflicts, status updates, and internal audit notes. I’m running the existing test suite now and will address any compatibility issues it exposes.

The offline test suite passes. I also verified the diff is clean; the implementation only changes account status modeling, the account service/controller, and note construction.

Implemented account freeze/unfreeze:

- Added `FROZEN` account status.
- Added `POST /api/accounts/{accountId}/freeze` with trimmed 1–500 character reason validation.
- Added `POST /api/accounts/{accountId}/unfreeze`.
- Enforced `accounts:write`, support assignment/admin authorization, and closed-account conflicts.
- Added internal audit notes for both actions.
- Both endpoints return the standard account representation.

Verified with `mvn -o -q test` — all tests pass.