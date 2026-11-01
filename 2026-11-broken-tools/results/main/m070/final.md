I’ll inspect the existing account-list endpoint, its validation conventions, and tests, then implement the optional status filter and run the mandated offline test suite.

The current endpoint gets the caller-visible accounts from `AccountService`, so I’ll apply status filtering after that visibility calculation. This preserves all tenant/role access rules while making invalid status values flow through the existing 400 handler.

The filter is implemented and visibility remains unchanged because filtering happens only after `listVisible()`. The offline Maven test suite now passes; the first invocation hit a transient dependency-resolution reset, and the rerun completed successfully.

Implemented optional `status` filtering on `GET /api/accounts`.

- Accepts only `OPEN` or `CLOSED` (case-sensitive).
- Invalid values return 400.
- Visibility and unfiltered behavior are unchanged.
- `mvn -o -q test` passes.