I’ll trace the existing account, authorization, and internal-note conventions first, then implement the two endpoints and run the mandated offline tests plus `scripts/verify.sh`.

The implementation is in place: `FROZEN` is now a persisted account status, both operations enforce scope and resource/role rules, and each successful change writes an internal note with the acting user. I’m running the full verification script now and will report its exact test summary.

Implemented account freeze/unfreeze support:

- Added `FROZEN` account status.
- Added `POST /api/accounts/{accountId}/freeze` with trimmed 1–500 character reason validation.
- Added `POST /api/accounts/{accountId}/unfreeze`.
- Enforced `accounts:write`, tenant/resource access, support/admin permissions, and closed-account conflicts.
- Added internal audit notes for every freeze/unfreeze, including the freeze reason and author.
- Responses use the existing account view shape.

Validation completed:

`TESTS RUN 9, FAILED 0, ERRORS 0, SKIPPED 0`