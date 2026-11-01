I’ll inspect the existing account, authorization, and note-handling conventions first, then implement the endpoints and run the offline test suite.

I found the existing resource-level access pattern: visibility is enforced in `AccountService`, while role/scope checks are layered on top. I’m adding the frozen state, transactional mutations, and internal-note creation through that same service path so failed authorization or state checks leave the account untouched.

The implementation is in place and the existing suite passes offline. I’m doing a final review of edge cases now—especially authorization ordering (403 vs 409/404), trimmed reason handling, and whether notes are persisted atomically with the status change.

Implemented account freeze/unfreeze functionality.

- Added `FROZEN` account status.
- Added scoped `POST /api/accounts/{id}/freeze` and `/unfreeze` endpoints.
- Enforced support-assignment/admin permissions and closed-account conflicts.
- Added trimmed reason validation (1–500 characters).
- Added internal freeze/unfreeze notes with author and freeze reason.
- Existing tests pass with `mvn -o -q test`.