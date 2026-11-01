I’ll inspect the existing account, authorization, and note-handling conventions, then implement the endpoints and run the mandated offline test suite.

The core implementation is in place: `FROZEN` status, scope-protected freeze/unfreeze routes, role/resource checks, closed-account conflicts, and internal audit notes with author and timestamp. I’m running the offline suite now and will adjust any compatibility issues it exposes.

Implemented account freeze/unfreeze:

- Added `FROZEN` account status.
- Added scope-protected `POST /api/accounts/{id}/freeze` and `/unfreeze`.
- Enforced support-assignment/admin permissions and closed-account conflicts.
- Added trimmed 1–500 character reason validation.
- Added internal audit notes for every action, including author and freeze reason.
- Responses use the existing account view shape.

Validation: `mvn -o -q test` completed with 9 tests run, 0 failures, 0 errors, and 0 skipped.