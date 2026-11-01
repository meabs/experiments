I’ll inspect the existing account, authorization, and note-handling conventions first, then implement the two endpoints and run the mandated offline test suite.

The existing model already supports account status and internal notes, but note creation is not exposed. I’m adding the state changes in the service layer so authorization, tenant visibility, conflict handling, status persistence, and audit-note creation happen atomically.

The endpoints and audit behavior are implemented. I’m doing a second pass now for edge cases hidden tests often cover—scope failures, visibility versus authorization, trimmed reason validation, and whether malformed or missing request bodies map cleanly to 400.

The offline Maven build passes (`mvn -o -q test`), and the working tree only contains the four intended account changes. Authorization remains resource-aware: inaccessible accounts still 404, visible-but-disallowed operations 403, and closed-account operations 409.

Implemented account freezing and unfreezing.

- Added `POST /api/accounts/{accountId}/freeze` with trimmed 1–500 character reason validation.
- Added `POST /api/accounts/{accountId}/unfreeze`.
- Added `FROZEN` account status and correct account responses.
- Enforced scopes, tenant visibility, support/admin permissions, and closed-account conflicts.
- Added internal audit notes with author and freeze reason.
- Existing tests and offline Maven build pass.