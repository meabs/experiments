I’m inspecting the existing case, authorization, and API conventions first, then I’ll implement the close endpoint and run the mandated offline test suite.

I found the existing case model and security pattern. I’m adding a dedicated support close route, trimming and validating the resolution explicitly (so validation is based on the trimmed value), enforcing tenant/assignee/admin access, and persisting a customer-visible comment in the same transaction.

The implementation is in place, including a separate controller so the route is exactly `/api/support/cases/{caseId}/close` (without inheriting the customer case prefix). I’m doing the final diff and test-count check now.

Implemented support case closure.

Changes:
- Added `POST /api/support/cases/{caseId}/close`.
- Validates trimmed resolutions to 1–2000 characters.
- Allows only the assigned support user or same-tenant admin.
- Returns 404 for inaccessible cases and 409 for already closed cases.
- Sets status to `CLOSED`.
- Saves the resolution as a customer-visible comment authored by the closer.

Verification:
- `mvn -o -q test`: 9 tests, 0 failures.
- Targeted `CaseApiTest`: 6 tests, 0 failures.