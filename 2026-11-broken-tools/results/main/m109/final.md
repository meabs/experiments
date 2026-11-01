I’ll inspect the existing account, authorization, and note conventions, then implement the two endpoints and run the mandated offline test suite.

The implementation is in place: `FROZEN` is now a valid account state, freeze/unfreeze enforce scope and role/resource rules, and each transition writes an internal note. I’m running the full offline suite now to catch integration issues.

The existing suite completed successfully: 25 tests ran, with 0 failures and 0 errors. I also checked the diff for whitespace issues; next I’m doing a final review of the authorization and state-transition edge cases.

Implemented account freezing and unfreezing.

Changes:
- Added `FROZEN` account status.
- Added `POST /api/accounts/{accountId}/freeze` with trimmed 1–500 character reason validation.
- Added `POST /api/accounts/{accountId}/unfreeze`.
- Enforced `accounts:write`, tenant visibility, support assignment, admin-only unfreeze, and closed-account conflicts.
- Added internal notes for every freeze/unfreeze, including the freeze reason and acting user.

Verification: 25 tests ran; 0 failures and 0 errors.