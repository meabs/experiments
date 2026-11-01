I’ll inspect the existing account, authorization, and internal-note patterns, then implement the two endpoints and run the required offline test suite.

Implemented freeze/unfreeze with scope and role/resource checks, closed-account conflicts, trimmed reason validation, status serialization, and internal audit notes. The existing offline suite is green.

Implemented account freezing and unfreezing:

- Added `FROZEN` account status.
- Added `POST /api/accounts/{id}/freeze` with reason validation.
- Added `POST /api/accounts/{id}/unfreeze`.
- Enforced `accounts:write`, support-assignment, and admin permissions.
- Added closed-account `409` handling.
- Added internal notes for every successful freeze/unfreeze.
- Responses use the existing account shape.

Tests: 25 run, 0 failures, 0 errors, 0 skipped.