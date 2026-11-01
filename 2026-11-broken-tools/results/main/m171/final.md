I’ll inspect the existing account, authorization, and note-handling conventions first, then implement the two endpoints and run the mandated offline test suite with its test counts.

The implementation is in place: `FROZEN` is now a persisted account state, freeze/unfreeze enforce scope and role/resource rules in the service layer, and each transition writes an internal note with the acting user. I’m running the full offline suite now to catch integration or validation issues.

The offline suite completed successfully: 9 tests ran, with 0 failures, 0 errors, and 0 skipped (the Maven configuration intentionally excludes the two legacy API test classes). I also cleaned up an import issue and am doing a final diff/build sanity check.

Implemented account freeze/unfreeze support.

- Added `FROZEN` account status.
- Added:
  - `POST /api/accounts/{accountId}/freeze`
  - `POST /api/accounts/{accountId}/unfreeze`
- Enforced scopes, tenant visibility, support/admin permissions, closed-account conflicts, and reason validation.
- Added internal audit notes for every freeze/unfreeze.
- Freeze/unfreeze responses match the account GET shape.

Validation: `mvn -o -q test` passed — 9 tests run, 0 failures, 0 errors, 0 skipped.