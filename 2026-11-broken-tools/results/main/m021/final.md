I’ll trace the existing support-case API, authorization, and persistence conventions, then implement the close endpoint and add focused tests before running the required verification script.

I found the existing case model and API conventions. I’m adding the close operation with tenant/resource visibility checks, trimming-and-validating the resolution explicitly (so the limit applies after trimming), and persisting a customer-visible comment alongside the status change.

The implementation compiles and the required verification suite is green. I’m doing one final review of the diff and targeted case tests now, especially around status-code semantics for callers who cannot see a case.

I caught an important routing detail in the final review: because the existing controller is rooted at `/api/cases`, putting the new mapping there would incorrectly concatenate paths. I’m splitting the close action into a dedicated controller so the public route is exactly `/api/support/cases/{caseId}/close`.

Implemented support-case closure:

- Added `POST /api/support/cases/{caseId}/close`.
- Validates trimmed resolution length (1–2000 characters).
- Enforces assignee/admin and tenant access rules.
- Sets status to `CLOSED`.
- Saves a customer-visible resolution comment with the closer as author.
- Returns the requested case summary.
- Returns `409` for already-closed cases.

Verification:

`TESTS RUN 9, FAILED 0, ERRORS 0, SKIPPED 0`