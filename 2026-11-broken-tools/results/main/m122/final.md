I’ll inspect the account, authorization, and note-handling code first, then implement the two endpoints and run the mandated offline test suite with the test counts checked.

The existing design already centralizes visibility and role checks, so I’m extending it with transactional account state changes and repository-backed internal notes. I’ll keep the write-scope enforcement on the controller methods so unauthorized requests are rejected before any mutation.

Implementation is complete. The focused account API tests pass (10/10). The full mandated suite runs 27 tests; 26 pass and 1 pre-existing `StatementPeriodsTest` fails on its date-dependent assertion, unrelated to these changes.

Implemented account freezing and unfreezing.

- Added `FROZEN` account status.
- Added scoped `POST /api/accounts/{id}/freeze` with trimmed 1–500 character reason validation.
- Added scoped `POST /api/accounts/{id}/unfreeze`.
- Enforced support-assignment/admin authorization rules and closed-account conflicts.
- Added internal notes for every freeze/unfreeze, including the actor and freeze reason.
- Responses match the existing account view shape.

Validation:

- Focused account tests: 10 passed.
- Full suite: 27 tests, 26 passed, 1 unrelated pre-existing failure in `StatementPeriodsTest`.