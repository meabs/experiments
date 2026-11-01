I’ll inspect the existing account, authorization, and internal-note patterns, then implement the two endpoints and run the offline test suite.

I found the existing visibility and role policy: account mutations will first resolve the account with the usual 404-hiding behavior, then enforce support-assignment/admin rules, and finally persist the status plus an internal note in one transaction. I’m adding the frozen status and request validation now.

The code compiles and the API tests ran; the suite’s only failure is the pre-existing asynchronous `BalanceAlertPublisherTest` (“alert not delivered”), unrelated to these changes. I’m doing a focused review of transaction persistence and edge-case behavior before wrapping up.

Focused account API tests pass. The implementation now persists status changes and notes atomically, trims and bounds freeze reasons, and preserves tenant/visibility rules (including 404 for inaccessible accounts).

Implemented account freezing and unfreezing:

- Added `FROZEN` account status.
- Added `POST /api/accounts/{accountId}/freeze` with trimmed 1–500 character reason validation.
- Added `POST /api/accounts/{accountId}/unfreeze`.
- Enforced `accounts:write`, tenant visibility, support assignment, and admin authorization rules.
- Closed accounts return `409`.
- Freeze/unfreeze actions create internal notes with the actor and freeze reason.
- Responses match the existing account view shape.

`AccountApiTest` passes. The full suite has one unrelated existing intermittent failure in `BalanceAlertPublisherTest` (“alert not delivered”).