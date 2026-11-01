I’ll inspect the existing account, authorization, and note-handling conventions first, then implement the two endpoints and run the mandated offline test suite.

I found the existing resource-level policy and note persistence model. I’m extending the account status enum and service transactionally so authorization and closed-account checks happen before any account or note mutation, with trimmed reason validation handled as a 400.

The implementation is in place. The targeted API regression tests pass; the full suite reaches one unrelated, date-sensitive pre-existing failure (`StatementPeriodsTest` expects September 2026 to be “last month,” while the environment date is November 2026). I’m doing a final diff/compile check now.

Implemented account freeze/unfreeze:

- Added `FROZEN` account status.
- Added secured endpoints:
  - `POST /api/accounts/{id}/freeze`
  - `POST /api/accounts/{id}/unfreeze`
- Enforced scopes, role/resource access, closed-account conflicts, and reason validation.
- Added internal audit notes with author and freeze reason.
- Responses match the existing account view shape.

Verification:
- Targeted API tests pass.
- Compilation and diff checks pass.
- Full test suite has one unrelated pre-existing date-sensitive failure in `StatementPeriodsTest`.