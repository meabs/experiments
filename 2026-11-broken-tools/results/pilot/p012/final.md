I’ll inspect the existing account, authorization, and note-handling conventions first, then implement the two endpoints and run the offline Maven test suite.

I found the existing resource-visibility and authorization pattern: service methods first resolve a visible account (preserving 404 behavior), then enforce the staff role, state conflict, and write an internal note in the same transaction. I’m extending that pattern with `FROZEN` status and the two POST routes.

The implementation is in place. The targeted account/closure API tests pass; the full suite reaches one pre-existing date-sensitive `StatementPeriodsTest` failure (it expects September 2026 to be “last month,” while the environment date is November 1, 2026), unrelated to these changes. I’m doing a final compile/diff check now.

Implemented account freeze/unfreeze:

- Added `FROZEN` account status.
- Added `POST /api/accounts/{accountId}/freeze` with trimmed 1–500 character reason validation.
- Added `POST /api/accounts/{accountId}/unfreeze`.
- Enforced `accounts:write`, tenant visibility, support/admin permissions, and closed-account conflicts.
- Added internal notes for every freeze/unfreeze, including the freeze reason and author.
- Responses use the existing account view shape.

Validation:
- Targeted API tests pass.
- Compilation succeeds.
- Full suite has one unrelated pre-existing date-sensitive `StatementPeriodsTest` failure.