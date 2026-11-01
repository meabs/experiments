I’ll inspect the existing account, authorization, and note-handling conventions first, then implement the two endpoints and run the required test/verification commands.

I found the existing resource-level convention: inaccessible accounts resolve as 404, while visible-but-disallowed actions are 403. I’m adding the state transition and note creation in the account service so the status update and internal note commit atomically.

The implementation is in place and the initial verification passed. I removed a redundant import, and I’m rerunning the mandated verification once more against the final tree so the reported counts match exactly.

Implemented account freeze/unfreeze support.

Changes:
- Added `FROZEN` account status.
- Added `POST /api/accounts/{accountId}/freeze` with trimmed 1–500 character reason validation.
- Added `POST /api/accounts/{accountId}/unfreeze`.
- Enforced `accounts:write`, support-assignment/admin authorization, and closed-account conflicts.
- Added internal notes for every freeze/unfreeze, including freeze reasons.
- Responses use the existing account representation.

Verification completed:

`TESTS RUN 9, FAILED 0, ERRORS 0, SKIPPED 0`