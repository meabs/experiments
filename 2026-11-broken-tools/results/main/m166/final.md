I’ll inspect the existing account, authorization, and note patterns, then implement the endpoints and run the mandated offline test suite.

I found the existing resource-level access rules and note persistence model. I’m adding the state transition in the service transaction so authorization, status checks, and the internal note are atomic.

The implementation is in place: `FROZEN` is now a persisted account status, both routes enforce `accounts:write`, transitions apply tenant/assignment rules and closed-account conflicts, and each successful action writes an internal note with the acting user. The offline suite is passing; I’m checking the final test totals and diff consistency now.

Implemented account freeze/unfreeze support:

- Added `FROZEN` account status.
- Added:
  - `POST /api/accounts/{accountId}/freeze`
  - `POST /api/accounts/{accountId}/unfreeze`
- Enforced `accounts:write` scope.
- Added reason validation and trimming.
- Enforced admin/support assignment permissions and closed-account conflicts.
- Added internal audit notes for every freeze/unfreeze.
- Frozen status is returned by existing account views.

Tests: 25 run, 0 failures, 0 errors, 0 skipped (`mvn -o -q test`).