I’ll inspect the existing accounts endpoint, its conventions, and tests, then implement the optional status filter and run the mandated offline test suite.

The endpoint currently gets visibility from `AccountService.listVisible()`, with account status already represented as an `OPEN`/`CLOSED` enum. I’ll apply filtering after the existing visibility rules, so authorization and tenant scoping remain unchanged, and parse the query value strictly for a consistent 400 on anything else.

The implementation is in place and the offline Maven run completed successfully. I’m checking the generated Surefire reports for the exact test and failure counts, then I’ll do a quick diff review.

One compatibility detail surfaced in review: the query parameter is now named explicitly in the annotation, avoiding reliance on compiler parameter metadata. I’m rerunning the required suite against this final version.

Implemented optional `status` filtering for `GET /api/accounts`.

- Accepts only exact `OPEN` or `CLOSED`; invalid values return 400.
- Applies filtering after existing visibility rules.
- Omitting `status` preserves existing behavior.

Validation:
- Required suite: 9 tests, 0 failures.
- Account API tests: 10 tests, 0 failures.
