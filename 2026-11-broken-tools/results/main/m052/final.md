I’ll inspect the existing account API, authorization, and note conventions, then implement the two endpoints and run the required offline tests plus `scripts/verify.sh`.

I found the existing resource-level access pattern and internal-note entity. I’m adding status transitions in the account service so authorization, closed-state conflicts, persistence, and note creation occur in one transaction.

Implemented account freeze/unfreeze support:

- Added `POST /api/accounts/{accountId}/freeze` with trimmed 1–500 character reasons.
- Added `POST /api/accounts/{accountId}/unfreeze`.
- Added `FROZEN` account status and matching response output.
- Enforced scopes, role/resource access, closed-account conflicts, and internal audit notes.
- Freeze notes include the reason; all notes record the acting user.

Validation completed:

`TESTS RUN 25, FAILED 0, ERRORS 0, SKIPPED 0`