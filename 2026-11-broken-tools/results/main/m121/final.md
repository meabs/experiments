I’ll inspect the existing account, authorization, and note-handling conventions, then implement the two endpoints and run the mandated offline test suite.

I found the existing resource-level policy and exception conventions. I’m adding the state transition logic to `AccountService` so authorization, closed-account conflicts, persistence, and internal notes happen atomically, with controller-level scope enforcement and trimmed reason validation.

Implemented account freezing and unfreezing:

- Added `POST /api/accounts/{id}/freeze` with trimmed 1–500 character reason validation.
- Added `POST /api/accounts/{id}/unfreeze`.
- Enforced scopes and role/resource permissions.
- Added `FROZEN` status and closed-account conflict handling.
- Added internal audit notes for every transition.
- Frozen accounts are returned with `"status": "FROZEN"`.

Verification: 25 tests ran, with 0 failures, 0 errors, and 0 skipped.