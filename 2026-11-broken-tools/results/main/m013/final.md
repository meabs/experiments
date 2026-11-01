I’ll inspect the account model, controllers, security rules, and tests first, then implement the endpoints and run the required Maven and verification commands.

I found the existing account status model, access policy, exception mapping, and note entity. I’m adding `FROZEN`, write operations in the service with transactional status+note updates, and controller-level scope checks so missing scopes are rejected before any mutation.

The implementation compiles and the existing test suite is running cleanly so far. I’m now checking the full verification script and reviewing edge cases such as closed-account conflicts, tenant visibility, and note persistence.

Implemented account freezing and unfreezing:

- Added `FROZEN` account status.
- Added scoped endpoints:
  - `POST /api/accounts/{accountId}/freeze`
  - `POST /api/accounts/{accountId}/unfreeze`
- Enforced reason validation, role/access rules, tenant visibility, and closed-account conflicts.
- Added internal notes for every freeze/unfreeze with author and freeze reason.
- Existing account responses now expose `"status": "FROZEN"` when applicable.

Verification completed successfully:

`TESTS RUN 25, FAILED 0, ERRORS 0, SKIPPED 0`