I’ll inspect the existing account, authorization, and note-handling conventions, then implement the two endpoints and run the mandated offline test suite.

I found the existing resource-level policy and exception conventions. I’m adding `FROZEN` to the account model, a validated trimmed request DTO, transactional service operations that enforce visibility/role/state rules, and internal-note creation with the caller identity.

The implementation compiles and the full test run is green. I’m doing a final review for hidden-case behavior (validation boundaries, authorization ordering, and note persistence) and checking the exact test totals before handing it back.

Implemented account freeze/unfreeze:

- Added `FROZEN` account status.
- Added scoped `POST /api/accounts/{id}/freeze` and `/unfreeze` endpoints.
- Enforced validation, visibility, support/admin permissions, and closed-account conflicts.
- Added internal audit notes with author and freeze reason.
- Account responses now expose updated status.

Tests: 25 passed, 0 failures/errors/skipped.