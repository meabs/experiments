I’ll inspect the existing account, authorization, and note-handling conventions, then implement the two endpoints and run the mandated Maven and verification checks.

The existing model has only `OPEN`/`CLOSED`; I’m extending it with `FROZEN`, adding transactional service methods that enforce visibility and role rules before mutation, and recording internal notes with the authenticated user as author. Input validation will trim first and reject blank or >500-character reasons.

Implementation is complete. The mandated suite reaches the new code successfully, while the repository’s pre-existing `StatementPeriodsTest` still fails; I’m doing the final verification run now and will report its exact totals.

Implemented account freezing/unfreezing:

- Added `FROZEN` account status.
- Added scoped `POST /api/accounts/{id}/freeze` and `/unfreeze` endpoints.
- Enforced admin/support authorization and closed-account conflicts.
- Added trimmed reason validation (1–500 characters).
- Added internal audit notes for every freeze/unfreeze.
- Responses use the existing account view shape.

Verification: `TESTS RUN 27, FAILED 1, ERRORS 0, SKIPPED 0`. The failure is pre-existing and unrelated: `StatementPeriodsTest.lastMonthsStatementIsDownloadable`.