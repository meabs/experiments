I’ll inspect the account model, security conventions, and existing endpoint/test patterns, then implement freeze/unfreeze with focused tests and run the required offline Maven suite.

I found the existing resource-level access and exception conventions. I’m adding the new status and write operations in the account service/controller, with validation and internal-note persistence handled transactionally so authorization or validation failures leave the account untouched.

The implementation is in place and the existing suite has completed successfully. I’m doing a final review of edge cases (scope/role ordering, closed-account conflicts, trimmed reason limits, and note contents) before handing it over.

Implemented account freezing and unfreezing.

Changes include:

- Added `FROZEN` account status.
- Added authenticated, `accounts:write`-protected endpoints:
  - `POST /api/accounts/{accountId}/freeze`
  - `POST /api/accounts/{accountId}/unfreeze`
- Enforced support/admin permissions and closed-account conflicts.
- Added trimmed reason validation (1–500 characters).
- Added internal notes for every freeze/unfreeze, including author and freeze reason.
- Responses use the existing account representation.

Verification: `25` tests run, `0` failures, `0` errors, `0` skipped.