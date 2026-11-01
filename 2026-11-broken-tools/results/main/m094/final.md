I’ll inspect the existing account-list endpoint, its validation conventions, and tests, then implement the optional status filter and run the mandated offline Maven tests.

The endpoint now parses the optional value strictly via `Account.Status.valueOf`, filters only after the existing visibility query, and relies on the project’s existing `IllegalArgumentException` → 400 mapping for invalid values. I’m running the full offline suite now.

Implemented optional `status` filtering for `GET /api/accounts`.

- Accepts only exact `OPEN` or `CLOSED`.
- Omitting `status` preserves existing behavior.
- Invalid values return HTTP 400.
- Existing visibility rules remain unchanged.

The mandated `mvn -o -q test` could not resolve the Spring Boot dependency offline, so no tests were executed.