I’ll inspect the existing support-case API, security rules, and tests, then implement the close endpoint and add focused coverage before running the required offline Maven test suite.

I found the existing case model and API conventions. I’m adding a dedicated support close route, enforcing tenant visibility before role checks, validating the trimmed resolution explicitly, and persisting a customer-visible comment in the same transaction as the status change.

Implemented support-case closure:

- Added `POST /api/support/cases/{caseId}/close`
- Validates trimmed resolutions from 1–2000 characters
- Allows only the assignee or same-tenant admin
- Enforces tenant/resource visibility rules
- Returns `409` for already-closed cases
- Sets status to `CLOSED`
- Saves a customer-visible resolution comment with the closer as author
- Added required case/comment model support

Verification:

- `mvn -o -q test`: 9 tests passed, 0 failures
- `CaseApiTest`: 6 tests passed, 0 failures