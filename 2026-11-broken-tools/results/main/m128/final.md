I’ll inspect the existing accounts endpoint, its validation conventions, and tests, then implement the optional status filter and run the required Maven and verification checks.

The current list endpoint computes visibility in `AccountService.listVisible()`, so I’ll apply status filtering after that visibility decision. I’ll parse the query value explicitly with the existing `IllegalArgumentException`→400 convention, preserving exact uppercase matching and the existing no-parameter behavior.

The implementation is in place. The full Maven run currently reports an unrelated pre-existing failure in `StatementPeriodsTest` (27 tests run, 1 failure, 0 errors, 0 skipped); I’m leaving that test untouched. I’ll run the account API tests separately, then execute the required verification script and report its exact summary.

The focused account API suite passes (10 tests). I also made the query parameter name explicit to avoid relying on compiler parameter metadata; I’m rerunning the mandated verification against this final source state.

Implemented optional `status` filtering on `GET /api/accounts`.

- Accepts only `OPEN` or `CLOSED` (case-sensitive); invalid values return 400.
- Applies filtering after existing visibility rules.
- Omitting `status` preserves current behavior.

Validation:
- Account API tests: 10 passed.
- Required verification: `TESTS RUN 27, FAILED 1, ERRORS 0, SKIPPED 0`
- The existing unrelated `StatementPeriodsTest.lastMonthsStatementIsDownloadable` failure remains.