I’ll inspect the existing controller/service conventions and tests, then implement the optional status filter with validation and run the required offline test suite.

The endpoint now parses only the existing `OPEN`/`CLOSED` enum values, filters after the existing visibility calculation, and lets the established `IllegalArgumentException` handler return 400 for any other spelling or value. I’m running the full offline tests now.

Implemented optional status filtering for `GET /api/accounts`.

- Accepts exactly `OPEN` or `CLOSED`.
- Invalid values return `400`.
- No status preserves existing behavior and visibility rules.
- Verified with `mvn -o -q test` successfully.