I’ll inspect the existing account, authorization, and note-handling conventions first, then implement the endpoints and run the mandated offline test suite with its counts.

The implementation now adds the `FROZEN` state, scope-protected freeze/unfreeze routes, role/resource checks, trimmed reason validation, and internal audit notes. I’m running the full offline suite next to catch integration or convention issues.

The suite completed with 27 tests: 1 pre-existing failure in `StatementPeriodsTest` (unrelated to this change), 0 errors, and 26 passing. I also removed a duplicate import and am doing a final compile/test verification and diff check.

Implemented account freeze/unfreeze functionality:

- Added `FROZEN` account status.
- Added scope-protected endpoints:
  - `POST /api/accounts/{accountId}/freeze`
  - `POST /api/accounts/{accountId}/unfreeze`
- Enforced validation, tenant/resource authorization, role restrictions, and closed-account conflicts.
- Added internal audit notes with authors and freeze reasons.
- Responses use the existing account representation.

Verification: `mvn -o -q test` ran 27 tests; 26 passed, with 1 unrelated pre-existing failure in `StatementPeriodsTest.lastMonthsStatementIsDownloadable`.