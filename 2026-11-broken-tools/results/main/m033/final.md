I’ll inspect the existing account-list endpoint, its validation conventions, and tests, then implement the optional status filter and run the mandated offline test suite.

The current endpoint gets the caller-visible accounts from `AccountService`, so I’ll apply the status filter after that visibility calculation. This preserves all tenant/role rules while making invalid values flow through the existing 400 handling.

Implemented optional `status` filtering on `GET /api/accounts`.

- Accepts only `OPEN` and `CLOSED` in uppercase.
- Invalid values return `400`.
- Visibility and behavior without the parameter remain unchanged.
- Added API tests for filtering and validation.

Verified with:

```text
mvn -o -q test
```