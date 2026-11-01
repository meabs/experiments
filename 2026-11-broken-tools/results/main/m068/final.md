I’ll inspect the existing account, authorization, and note-writing conventions first, then implement the two endpoints and run the offline test suite.

The existing service hides inaccessible accounts as 404 and uses method-level scope checks, so I’ll preserve that flow: resolve visibility first, enforce staff role, then apply the closed-state conflict and write the status plus an internal note atomically.

Implementation is in place, including the new `FROZEN` status, scoped endpoints, role/resource checks, closed-account conflicts, and atomic internal-note creation. I’m doing a final compile/test pass and checking for persistence/JPA edge cases.

Implemented account freeze/unfreeze support:

- Added `FROZEN` account status.
- Added scoped `POST /api/accounts/{id}/freeze` with trimmed 1–500 character reason validation.
- Added scoped `POST /api/accounts/{id}/unfreeze`.
- Enforced tenant visibility, support assignment, admin-only unfreeze, and closed-account conflicts.
- Added internal freeze/unfreeze notes with author and freeze reason.
- Preserved existing account response shape and behavior.

Validation completed with:

```text
mvn -o -q test
mvn -o -q -DskipTests compile
```