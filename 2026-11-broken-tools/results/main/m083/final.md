I’ll inspect the existing account, authorization, and note-handling conventions, then implement the two endpoints and run the mandated offline test suite with its test counts.

I found the existing resource-level policy and note model. I’m adding the state transition logic to `AccountService`, keeping authorization and scope checks aligned with the existing conventions, and extending the account status enum plus internal-note creation.

The implementation is in place. The first Maven attempt hit a transient local dependency-resolution reset; I reran the mandated command successfully and am checking the generated Surefire reports to confirm the exact totals before handing off.

Implemented account freeze/unfreeze:

- Added `POST /api/accounts/{id}/freeze` with trimmed 1–500 character reason validation.
- Added `POST /api/accounts/{id}/unfreeze`.
- Added `FROZEN` account status and account-shaped responses.
- Enforced `accounts:write`, tenant visibility, support/admin permissions, and closed-account conflicts.
- Added internal notes for every freeze/unfreeze with author and freeze reason.

Tests: `25` run, `0` failures, `0` errors, `0` skipped.