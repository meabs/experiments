I’m reviewing the existing account, authorization, and note-handling conventions first, then I’ll implement the endpoints and run the offline test suite.

I found the existing resource-level policy and transaction conventions. I’m adding freeze/unfreeze as account mutations in the service so authorization, closed-state checks, status changes, and internal-note creation happen atomically.

The implementation is in place and the account API tests pass. The full suite reaches an unrelated pre-existing date-sensitive failure in `StatementPeriodsTest` (it expects September 2026 to remain downloadable, while the current date is November 2026); no freeze-related failures or startup errors appeared.

Implemented account freezing and unfreezing.

Changes include:

- Added `FROZEN` account status.
- Added scoped endpoints:
  - `POST /api/accounts/{accountId}/freeze`
  - `POST /api/accounts/{accountId}/unfreeze`
- Enforced support/admin authorization rules and closed-account conflicts.
- Added trimmed reason validation (1–500 characters).
- Added internal notes for every freeze/unfreeze, including the freeze reason.
- Responses use the existing account representation.

`AccountApiTest` and compilation pass. The full suite has one unrelated pre-existing date-sensitive failure in `StatementPeriodsTest`.