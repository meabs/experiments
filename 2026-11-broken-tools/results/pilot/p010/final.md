I’ll trace the existing account-list endpoint and its validation conventions, then implement the optional status filter and run the prescribed offline test suite.

The endpoint currently has no query binding, and invalid-input handling already maps `IllegalArgumentException` to 400. I’m adding a case-sensitive enum parse at the controller boundary and applying the filter after the existing visibility calculation, so tenant/role access remains unchanged.

The implementation is in place and the full offline Maven test suite passes. I’m doing a final diff check for formatting and confirming only the two account-list classes changed.

Implemented optional status filtering for `GET /api/accounts`.

- Supports exact values `OPEN` and `CLOSED`.
- Omitting `status` preserves existing behavior.
- Invalid values return `400`.
- Existing visibility rules remain unchanged.
- `mvn -o -q test` passes.