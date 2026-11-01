I’ll inspect the existing support-case API, security rules, and tests, then implement the close endpoint and run the mandated offline test suite.

I found the existing case model and security conventions. I’m adding a dedicated staff close route, enforcing tenant/assignee access at the resource level, and persisting the trimmed resolution as a customer-visible comment in the same transaction.

The implementation is in place and the full offline Maven suite passes. I also tightened the role check so an admin who happens to carry a support role still has admin authority, while cross-tenant and unassigned support access remains hidden as not-found.

Implemented support-case closure:

- Added `POST /api/support/cases/{caseId}/close`
- Validates trimmed resolution length (1–2000)
- Allows only the assignee or same-bank admin
- Returns 404 for inaccessible cases and 409 for already-closed cases
- Sets status to `CLOSED`
- Saves a customer-visible resolution comment authored by the closer
- Returns the requested case summary

Verified with `mvn -o -q test` — all tests pass.