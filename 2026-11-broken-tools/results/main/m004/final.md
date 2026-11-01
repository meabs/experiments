I’ll inspect the existing account, authorization, and note-handling conventions first, then implement the two endpoints and run the mandated Maven and verification checks.

The existing design puts resource visibility in `AccountService` and role checks in controllers. I’ll preserve that pattern: scope enforcement via `@PreAuthorize`, visibility before action authorization, closed-state conflicts before writes, and note creation in the same transaction as the status change.

The implementation compiles and the existing suite is green. I’m doing a final verification pass now, including the repository’s required `scripts/verify.sh`, and checking the exact test totals before reporting.

Implemented account freezing and unfreezing.

Changes include:

- Added `FROZEN` account status.
- Added `POST /api/accounts/{accountId}/freeze` with trimmed 1–500 character reason validation.
- Added `POST /api/accounts/{accountId}/unfreeze`.
- Enforced `accounts:write`, tenant visibility, support/admin permissions, and closed-account conflicts.
- Added internal freeze/unfreeze notes with author and freeze reason.
- Both endpoints return the standard account view.

Verification:

`TESTS RUN 25, FAILED 0, ERRORS 0, SKIPPED 0`