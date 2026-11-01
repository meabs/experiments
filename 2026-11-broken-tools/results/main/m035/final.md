I’m inspecting the existing account, authorization, and note-handling conventions first, then I’ll implement the endpoints and run the offline test suite.

The existing model has only `OPEN`/`CLOSED`, and notes are read-only entities with no creation path. I’m adding `FROZEN`, transactional account operations that enforce role/tenant visibility, and internal-note creation in the same transaction.

Implemented account freezing and unfreezing:

- Added `FROZEN` account status.
- Added scoped `POST /api/accounts/{id}/freeze` and `/unfreeze` endpoints.
- Enforced support-assignment/admin permissions and closed-account conflicts.
- Added internal notes with author and freeze reason.
- Added trimmed reason validation (1–500 characters).
- Responses use the existing account view shape.

Compilation succeeds. The test suite ran 27 tests with 1 pre-existing unrelated failure in `StatementPeriodsTest`; 26 passed.