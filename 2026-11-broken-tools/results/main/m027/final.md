I’ll inspect the existing account, authorization, and internal-note flows, then implement the two endpoints and run the offline Maven test suite.

I found the existing resource-level policy and note entity. I’m adding `FROZEN` to the account state, transactional service operations that enforce visibility/role/state rules, and internal-note creation tied to the current user.

The implementation is in place and the existing suite already passes. I also adjusted validation ordering so authorization and closed-state conflicts take precedence, preserving the API’s 403/404/409 semantics before checking the freeze reason.

Implemented account freeze/unfreeze support.

- Added `FROZEN` account status.
- Added:
  - `POST /api/accounts/{accountId}/freeze`
  - `POST /api/accounts/{accountId}/unfreeze`
- Enforced scopes, tenant visibility, support/admin permissions, closed-account conflicts, and reason validation.
- Added internal notes for every freeze/unfreeze with author and freeze reason.
- Existing account response shape now reports `"status": "FROZEN"`.

Verified with:

```text
mvn -o -q test
```