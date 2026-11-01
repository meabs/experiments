I’m reviewing the existing account, authorization, and internal-note conventions first, then I’ll implement the two endpoints and run the offline test suite.

The implementation is in place: `FROZEN` is now a valid account state, both write endpoints enforce scope and resource-level roles, closed accounts return conflicts, and each transition writes an internal audit note. I’m checking the full test/build result and reviewing edge cases such as trimmed reason length and visibility.

The build compiles cleanly, and I adjusted validation so the 500-character limit is applied after trimming (leading/trailing whitespace no longer causes a false rejection). The existing offline test suite is also passing.

Implemented account freeze/unfreeze support.

Changes include:

- Added `FROZEN` account status.
- Added:
  - `POST /api/accounts/{accountId}/freeze`
  - `POST /api/accounts/{accountId}/unfreeze`
- Enforced `accounts:write` scope.
- Enforced support-assignment/admin authorization rules.
- Added closed-account conflict handling.
- Added trimmed reason validation (1–500 characters).
- Added internal audit notes for every freeze/unfreeze.
- `GET /api/accounts/{accountId}` now returns `"status": "FROZEN"` appropriately.

`mvn -o -q test` and compilation pass successfully.