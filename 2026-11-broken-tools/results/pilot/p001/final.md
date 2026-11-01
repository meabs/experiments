I’ll inspect the existing account, authorization, and note-handling conventions, then implement the two endpoints and run the mandated offline test suite.

I found the existing resource-level policy and transaction conventions. I’m adding the new status and mutations in the account service so authorization, closed-state checks, status changes, and internal-note creation occur atomically.

Implemented account freeze/unfreeze support:

- Added `FROZEN` account status.
- Added secured `POST /api/accounts/{accountId}/freeze` with trimmed 1–500 character reason validation.
- Added secured `POST /api/accounts/{accountId}/unfreeze`.
- Enforced scope, role, assignment, tenant, and closed-account rules.
- Added internal audit notes for every freeze/unfreeze.
- Existing account responses now expose `"status": "FROZEN"` appropriately.

Verified with:

```text
mvn -o -q test
```

All tests pass.