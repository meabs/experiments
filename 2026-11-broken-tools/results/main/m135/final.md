I’ll inspect the existing case, security, and API conventions, then implement the close endpoint and run the required offline test suite.

I found the existing case model and tenant access conventions. I’m adding a dedicated support close controller so the public `/api/cases` behavior stays unchanged, with authorization distinguishing hidden cross-tenant/non-assignee cases from visible-but-forbidden customers.

The implementation is in place and the full offline Maven suite passes. I’m doing a final review of edge cases—especially tenant masking, repeated closes, and trimming/length validation—before handing it over.

Implemented support case closure:

- Added `POST /api/support/cases/{caseId}/close`
- Validates trimmed resolution length: 1–2000 characters
- Allows only the assignee or same-tenant admin
- Masks inaccessible cases with 404
- Returns 409 for already closed cases
- Saves the resolution as a customer-visible comment authored by the closer
- Updates status to `CLOSED`
- Returns the requested case summary fields

`mvn -o -q test` passes.