I’ll trace the existing support-case model, authorization patterns, and tests first, then implement the close endpoint and add focused coverage before running the mandated offline Maven test suite.

The endpoint and persistence path are in place: it enforces tenant isolation, assignee/admin authorization, trimmed resolution limits, closed-state conflicts, and writes a customer-visible comment authored by the closer. I’m running the full offline suite now to catch wiring or convention mismatches.

The first pass exposed a routing detail: because the existing controller is rooted at `/api/cases`, the new support route needs its own controller to produce exactly `/api/support/cases/{caseId}/close`. I split that endpoint into a dedicated controller and verified the project compiles. The full suite has one unrelated date-sensitive pre-existing failure (`StatementPeriodsTest` expects September 2026 while the system date is November 2026).

Implemented support-case closure:

- Added `POST /api/support/cases/{caseId}/close`.
- Enforced assignee/admin and same-tenant authorization.
- Added trimmed 1–2000 character resolution validation.
- Sets status to `CLOSED`.
- Saves a customer-visible resolution comment authored by the closer.
- Returns the requested case summary.
- Returns 409 for already-closed cases without adding another comment.

Verification: compilation and API tests pass. The full suite still has one unrelated pre-existing date-sensitive failure in `StatementPeriodsTest` (expects September 2026, while the current date is November 2026).