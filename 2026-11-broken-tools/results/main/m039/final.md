I’ll inspect the existing account, authorization, and note-handling conventions, then implement the two endpoints and run the mandated offline test suite.

I found the existing resource-level pattern: scope checks on controllers, visibility via `getVisible`, then role checks in the service/controller, with API exceptions mapped to 400/403/409. I’m adding `FROZEN` to the account state model, persisting internal audit notes, and validating the trimmed reason explicitly so surrounding whitespace doesn’t count toward the 500-character limit.

The implementation is in place. I’m now checking the full offline suite’s result summary and doing a focused review for edge cases such as missing/blank reasons, closed-account conflicts, tenant visibility, and authorization ordering.

Implemented account freeze/unfreeze support:

- Added `FROZEN` account status.
- Added:
  - `POST /api/accounts/{accountId}/freeze`
  - `POST /api/accounts/{accountId}/unfreeze`
- Enforced scopes and role/resource authorization.
- Added trimmed 1–500 character reason validation.
- Closed accounts return 409 without changes.
- Added internal audit notes for every freeze/unfreeze, including the freeze reason and actor.
- Account responses now expose `"status": "FROZEN"` appropriately.

Validation: `mvn -o -q test` passed — 9 tests, 0 failures, 0 errors, 0 skipped.