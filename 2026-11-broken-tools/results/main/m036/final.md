I’ll inspect the existing account, authorization, and note-handling conventions first, then implement the two endpoints and run the offline Maven test suite.

The model now supports `FROZEN`, and I’ve added scoped freeze/unfreeze operations with role/resource checks, closed-account conflicts, and internal audit notes. I’m running the existing suite now to catch integration or persistence issues.

The API-focused tests pass. The full suite reaches one pre-existing date-sensitive failure in `StatementPeriodsTest` (it expects September 2026 to be “last month,” while the environment date is November 1, 2026); it is unrelated to these changes. I’m doing a final diff/compile sanity check.

Implemented account freeze/unfreeze support:

- Added `FROZEN` account status.
- Added:
  - `POST /api/accounts/{accountId}/freeze`
  - `POST /api/accounts/{accountId}/unfreeze`
- Enforced `accounts:write`, tenant visibility, support assignment, and admin permissions.
- Added validation for trimmed freeze reasons (1–500 characters).
- Closed accounts return `409` without changes.
- Freeze/unfreeze operations create internal audit notes with the acting user.
- Account responses now expose `"status": "FROZEN"` appropriately.

Compilation succeeds. API tests pass; the full suite has one unrelated pre-existing date-sensitive failure in `StatementPeriodsTest`.