I’ll inspect the case model, security rules, and existing support-case endpoints/tests, then implement the close flow and run the offline test suite.

I found the existing case controller and security conventions. I’m adding a transactional close operation that tenant-filters the case, distinguishes 404/403 correctly, validates the trimmed resolution length, updates status once, and records a customer-visible comment.

The close route is now a separate controller so its absolute URL is exactly `/api/support/cases/{caseId}/close` (the existing case controller’s `/api/cases` prefix would otherwise be inherited). The implementation compiles and the offline suite is passing.

Implemented support-case closure:

- Added `POST /api/support/cases/{caseId}/close`
- Validates trimmed resolutions to 1–2000 characters
- Allows only the assigned support user or same-tenant admins
- Returns 404 for inaccessible tenant cases, 403 for unauthorized same-tenant users
- Prevents reopening/duplicate closure with 409
- Sets status to `CLOSED`
- Saves a customer-visible resolution comment with the closer as author

Verified with `mvn -o -q test`.