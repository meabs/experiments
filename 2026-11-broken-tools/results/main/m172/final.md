I’ll inspect the existing support-case API, security checks, and persistence model, then implement the close endpoint with validation and focused tests.

I found the existing case entity and comment table, plus the project’s 404/403/409 conventions. I’m adding the close route under `/api/support/cases`, enforcing tenant visibility before permission checks, and recording the trimmed resolution as a public comment.

The implementation is in place and compiles under the project’s offline test command. I’m doing one extra verification pass for edge-case ordering (tenant hiding, authorization, validation, and repeat-close conflict) before handing it back.

Implemented support-case closure:

- Added `POST /api/support/cases/{caseId}/close`
- Validates trimmed resolution length (1–2000 characters)
- Allows only the case assignee or same-tenant admin
- Enforces tenant/resource visibility rules
- Returns the requested case summary with status `CLOSED`
- Records the resolution as a customer-visible comment authored by the closer
- Returns `409` for already-closed cases without adding another comment

Verified with:

```text
mvn -o -q -DskipTests=false test
```

All existing tests pass.