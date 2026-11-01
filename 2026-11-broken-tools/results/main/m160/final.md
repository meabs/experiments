I’ll inspect the existing support-case API, security conventions, and tests first, then implement the endpoint and run the mandated verification.

The existing case model stores status as a string and comments as separate entities. I’m adding a dedicated support close controller, enforcing tenant/assignee/admin access, trimming and validating the resolution explicitly, then persisting a public comment atomically with the status change.

The implementation is in place. The Maven suite currently reports 27 tests with 1 pre-existing failure in `StatementPeriodsTest` (its date-sensitive fixture expects September 2026 to be last month while the environment date is November 2026); no case-related tests fail. I’m running the repository’s required verification script now.

Implemented `POST /api/support/cases/{caseId}/close`.

- Enforces tenant, assignee/admin, and write-scope rules.
- Trims and validates resolutions to 1–2000 characters.
- Changes status to `CLOSED`.
- Saves a customer-visible resolution comment authored by the closer.
- Returns the requested case summary.
- Returns 409 for already-closed cases.

Verification: `TESTS RUN 27, FAILED 1, ERRORS 0, SKIPPED 0`

The sole failure is the pre-existing date-sensitive `StatementPeriodsTest`; all case/API tests pass.