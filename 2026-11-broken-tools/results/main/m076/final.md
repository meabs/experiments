I’ll inspect the existing case, authorization, and comment patterns, then implement the endpoint and run the mandated offline test suite.

I found the existing case model and comment table. I’m adding a dedicated support-closing route, enforcing tenant visibility before action authorization, and persisting the trimmed resolution as a customer-visible comment in the same transaction.

The implementation compiles and the case API tests pass. The full suite still has one pre-existing failure in `StatementPeriodsTest` (date-dependent statement download assertion); I’m leaving it unchanged as required and doing a final diff/validation check.

Implemented support case closure:

- Added `POST /api/support/cases/{caseId}/close`
- Validates trimmed resolution length: 1–2000 characters
- Allows only the assigned support user or same-tenant admin
- Returns 404 across tenants, 403 for unauthorized staff/customers, and 409 if already closed
- Saves the resolution as a customer-visible comment authored by the closer
- Sets case status to `CLOSED`

Validation:
- `CaseApiTest`: passed
- Full suite: 27 tests run, 1 unrelated pre-existing failure in `StatementPeriodsTest` (date-dependent assertion)