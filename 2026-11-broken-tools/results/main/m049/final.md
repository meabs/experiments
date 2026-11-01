I’ll inspect the existing account, authorization, and note-handling conventions first, then implement the two endpoints and run the mandated test/verification commands.

I found the existing resource-level access pattern: account visibility is resolved to 404 first, then role-specific actions return 403, while method security enforces scopes before any mutation. I’m implementing the state transitions in the account service transaction so status and internal-note creation succeed or fail together.

The implementation is complete and the full verification suite has passed. I’m doing one final clean offline Maven run/check now so the handoff includes an unambiguous test result.

Implemented account freeze/unfreeze support:

- Added `FROZEN` account status.
- Added scoped `POST /api/accounts/{id}/freeze` with trimmed 1–500 character reason validation.
- Added scoped `POST /api/accounts/{id}/unfreeze`.
- Enforced support/admin permissions and closed-account conflicts.
- Added internal audit notes for both operations.
- Frozen status is returned by existing account views.

Verification:

`TESTS RUN 25, FAILED 0, ERRORS 0, SKIPPED 0`