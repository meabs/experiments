I’ll inspect the case model, security rules, and existing support-case endpoints, then implement the close flow and run the mandated offline Maven tests.

I found the existing case entity/repository and the project’s 400/403/404/409 exception conventions. I’m adding the close action under the requested `/api/support/cases/...` path, with tenant and assignee checks, trimmed resolution validation, status mutation, and a customer-visible comment in the same transaction.

The implementation is in place and the existing suite passes with `mvn -o -q test`. I’m doing a final review of edge-case precedence and the exact response/security behavior before handing it back.

Implemented support-case closure:

- Added `POST /api/support/cases/{caseId}/close`
- Validates and trims resolutions to 1–2000 characters
- Allows only the assigned support user or same-tenant admin
- Enforces tenant isolation and required write scope
- Sets status to `CLOSED`
- Saves a customer-visible resolution comment
- Returns 409 for already closed cases
- Added entity support for closing cases and creating comments

Verified with:

```bash
mvn -o -q test
```