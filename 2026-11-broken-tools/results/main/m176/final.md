I’ll inspect the existing account API, authorization, and note patterns, then implement the two endpoints and run the mandated offline test suite.

I found the account status, visibility policy, and note persistence paths. I’m adding the lifecycle operations in the account service so authorization, closed-account conflicts, status mutation, and internal-note creation happen atomically.

The endpoints and persistence changes are in place. Validation trims the reason before enforcing 1–500 characters; scope checks remain at the controller boundary, while resource-role checks and closed-account conflicts occur inside the transaction. I’m doing a final test/diff check now.

Implemented account freeze/unfreeze functionality:

- Added `POST /api/accounts/{accountId}/freeze`
  - Validates trimmed reason length (1–500)
  - Supports admins and assigned support users
  - Sets status to `FROZEN`
- Added `POST /api/accounts/{accountId}/unfreeze`
  - Admin-only
  - Sets status to `OPEN`
- Both require `accounts:write`
- Closed accounts return `409`
- Freeze/unfreeze actions create internal notes with author and timestamp
- Added `FROZEN` account status
- Existing tests pass with `mvn -o -q test`