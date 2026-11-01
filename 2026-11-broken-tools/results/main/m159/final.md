I’ll inspect the existing account model, authorization checks, and tests, then implement the two endpoints with matching validation, notes, and status behavior. I’ll run the mandated offline Maven test suite afterward.

I found the existing resource-level policy and note persistence model. I’m adding the state transition in `AccountService` so authorization, closed-state checks, status updates, and note creation happen in one transaction; the controller will expose the same `AccountView` shape as GET.

Implemented account freeze/unfreeze support:

- Added `FROZEN` account status.
- Added secured endpoints:
  - `POST /api/accounts/{accountId}/freeze`
  - `POST /api/accounts/{accountId}/unfreeze`
- Enforced scope, role, assignment, closed-account, and reason validation rules.
- Added internal notes for every freeze/unfreeze, including freeze reasons.
- Responses use the existing account view shape.
- Verified with `mvn -o -q test` (passes).