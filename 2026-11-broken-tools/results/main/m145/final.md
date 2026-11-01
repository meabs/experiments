I’ll inspect the existing support-case API, security rules, and tests, then implement the close endpoint and run the required offline test suite.

I found the existing case model and security conventions. I’m adding a staff-only controller under `/api/support/cases`, with tenant-aware 404 handling, role/resource 403 checks, trimmed resolution validation, and an atomic case-status/comment update.

I tightened the resource check so a customer attempting another customer’s case gets the API’s normal indistinguishable 404, while a customer attempting their own case is correctly forbidden. The close operation remains transactional, so a failed second close cannot add another comment.

Implemented support-case closure:

- Added `POST /api/support/cases/{caseId}/close`.
- Validates trimmed resolution length (1–2000 characters).
- Allows only the case assignee or same-tenant admin.
- Returns 404 for inaccessible cases, 403 for unauthorized users, and 409 for already-closed cases.
- Sets status to `CLOSED` and records a customer-visible resolution comment with the closer as author.

Files changed:
- [SupportCaseController.java](~/code/benchmark/brk-work/main/m145/ws/src/main/java/com/example/accounts/cases/SupportCaseController.java)
- [SupportCase.java](~/code/benchmark/brk-work/main/m145/ws/src/main/java/com/example/accounts/cases/SupportCase.java)
- [CaseComment.java](~/code/benchmark/brk-work/main/m145/ws/src/main/java/com/example/accounts/cases/CaseComment.java)

Tests: 9 run, 0 failures, 0 errors.