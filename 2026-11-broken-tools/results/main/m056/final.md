I’ll inspect the existing support-case API, security conventions, and tests, then implement the endpoint and run the mandated offline test suite.

I found the existing case model and API conventions. I’m adding a dedicated support close action with tenant-aware lookup, role/assignee checks, trimmed resolution validation, status transition, and a customer-visible comment in the same transaction.

Implemented support-case closure:

- Added `POST /api/support/cases/{caseId}/close`
- Validates trimmed resolutions from 1–2000 characters
- Allows only the case assignee or same-tenant admin
- Returns 404 across tenants, 403 for unauthorized same-tenant users
- Transitions status to `CLOSED`
- Prevents repeat closure with 409
- Saves a customer-visible resolution comment authored by the closer

`git diff --check` passes. The mandated Maven test command could not run because Maven failed resolving the Spring Boot dependency offline (`Connection reset`).