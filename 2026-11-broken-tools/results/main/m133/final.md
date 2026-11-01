I’ll inspect the existing case, comment, and authorization patterns, then implement the endpoint and run the offline test suite.

I found the existing case model and security conventions. I’m adding a staff-only support endpoint, enforcing tenant/assignee authorization at the resource level, and recording the trimmed resolution as a customer-visible comment in the same transaction.

The implementation compiles and the full offline suite passes. I’m making one final consistency check against the README’s anti-enumeration rule so unauthorized support users get the same non-disclosing behavior as other resources.

Implemented support case closure.

Changes:
- Added `POST /api/support/cases/{caseId}/close`.
- Validates trimmed resolution length (1–2000 characters).
- Allows only the assigned support user or same-tenant admin.
- Returns 404 for inaccessible cases, 409 for already closed cases.
- Sets status to `CLOSED` and saves a customer-visible resolution comment.
- Added case/comment persistence helpers.

All tests pass with `mvn -o -q test`.