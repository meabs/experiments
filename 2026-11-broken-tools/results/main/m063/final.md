I’ll inspect the existing account, authorization, and note-handling conventions first, then implement the two endpoints and run the mandated Maven and verification checks.

The existing model stores account status as a string and already has repository support for internal notes, but no note creation path. I’ll add `FROZEN`, a transactional service operation that enforces visibility/state/role rules, and controller-level request validation for the trimmed reason.

The implementation is in place: freeze/unfreeze are scope-protected, resource-visible, tenant-safe, and transactional; closed accounts return 409 before mutation; notes are internal and attributed to the caller. The returned view is the same `AccountView`, so frozen status is exposed consistently. I’m now running the full verification script and checking its exact test counts.

Implemented account freeze/unfreeze support.

Changes include:

- Added `FROZEN` account status.
- Added `POST /api/accounts/{accountId}/freeze` with trimmed 1–500 character reason validation.
- Added `POST /api/accounts/{accountId}/unfreeze`.
- Enforced `accounts:write`, tenant visibility, support assignment, and admin permissions.
- Closed accounts return 409 without changes.
- Freeze/unfreeze actions create internal notes attributed to the acting user.
- Responses use the existing account view shape.

Verification completed successfully:

`TESTS RUN 9, FAILED 0, ERRORS 0, SKIPPED 0`