I’ll inspect the account model, authorization conventions, and existing tests first, then implement the two endpoints and add focused coverage. I’ll run the mandated offline Maven test suite before wrapping up.

The existing service already centralizes tenant/resource visibility, and the API maps validation, forbidden, and conflict errors to the required statuses. I’m extending that path with a `FROZEN` state, transactional freeze/unfreeze operations, and internal-note creation so authorization and state checks happen before any mutation.

The implementation is in place. The mandated offline test command is currently blocked before compilation because Maven cannot resolve the Spring Boot 3.5.6 descriptor from the local cache (`Connection reset`), so I’m doing a source-level review now and will report that environmental limitation clearly.

Implemented account freeze/unfreeze support:

- Added `FROZEN` account status.
- Added `POST /api/accounts/{accountId}/freeze` with trimmed 1–500 character reason validation.
- Added `POST /api/accounts/{accountId}/unfreeze`.
- Enforced `accounts:write`, support assignment/admin freeze rules, admin-only unfreeze, and closed-account conflicts.
- Added internal notes recording actor and freeze reason.
- Account responses now expose `"status": "FROZEN"` appropriately.

`git diff --check` passes. The mandated `mvn -o -q test` could not start because Maven failed resolving the cached Spring Boot descriptor (`Connection reset`).