I’ll inspect the account controller, service, and existing tests/conventions first, then implement the optional status filter and run the prescribed offline test suite.

The existing visibility logic already centralizes tenant/role filtering in `AccountService.listVisible()`. I’ll apply the status predicate after that method returns, so the new filter cannot broaden access; invalid values will use the project’s existing `IllegalArgumentException`→400 convention.

The implementation is in place: `status` is parsed strictly through `Account.Status.valueOf`, then applied only to the already-visible account list. I also verified the existing offline test suite passes.

Implemented optional `status` filtering on `GET /api/accounts`.

- Accepts only exact `OPEN` or `CLOSED`.
- Invalid values return `400`.
- Visibility and behavior without the parameter remain unchanged.
- Verified with `mvn -o -q test` (passes).