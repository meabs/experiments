I’ll inspect the existing support-case model, controller, security checks, and tests, then implement the close endpoint and run the offline Maven suite.

The endpoint and persistence changes are in place: authorized assignee/admin closure, tenant/resource visibility checks, trimmed resolution validation, `CLOSED` transition, and customer-visible comment creation. I’m running the full offline test suite now.

The case-focused tests pass. The full suite has one pre-existing, unrelated failure in `StatementPeriodsTest` (its fixed September 2026 expectation is currently considered non-downloadable); no case/API failures occurred. I’m doing a final review of the diff and endpoint behavior.

Implemented `POST /api/support/cases/{caseId}/close` with:

- Assignee/admin authorization and tenant isolation
- Trimmed 1–2000 character resolution validation
- `CLOSED` status transition
- Customer-visible resolution comment
- 409 for already closed cases
- Appropriate 403/404 access behavior

Case-focused tests pass. The full suite still has one unrelated existing `StatementPeriodsTest` failure due to its fixed-date expectation.