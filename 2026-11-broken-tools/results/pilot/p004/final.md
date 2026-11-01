I’ll inspect the existing case, authorization, and comment patterns, then implement the endpoint and run the offline test suite.

I found the existing case entity/repository and the API’s tenant/visibility rules. I’m adding a dedicated support close route, enforcing trimmed resolution length, preserving 404-vs-403 resource hiding, and recording a customer-visible comment in the same transaction.

The implementation is in place, and `mvn -o -q test` now passes. The close operation updates the case and creates a non-internal comment atomically; unauthorized cross-tenant or non-visible cases remain indistinguishable from missing cases.

Implemented support case closure:

- Added `POST /api/support/cases/{caseId}/close`
- Validates trimmed resolution length (1–2000 characters)
- Allows only the assigned support user or same-tenant admin
- Returns 404 for inaccessible cases and 403 for visible customers attempting closure
- Returns 409 for already closed cases
- Persists a customer-visible resolution comment
- Returns the requested case summary

Verified with `mvn -o -q test` successfully.