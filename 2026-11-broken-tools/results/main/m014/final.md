I’ll inspect the current account-list endpoint, its validation conventions, and tests, then implement the optional status filter and run the offline Maven test suite.

The existing visibility logic is centralized in `AccountService.listVisible()`. I’ll apply the status condition only after that visibility-filtered result, so the new parameter cannot broaden access. Invalid values will be parsed strictly through the existing 400 exception convention.

Implemented optional status filtering on `GET /api/accounts`.

- Supports only exact `OPEN` and `CLOSED` values.
- Invalid values return `400`.
- Filtering occurs after existing visibility rules.
- Omitting `status` preserves current behavior.

Tests pass with `mvn -o -q test`.