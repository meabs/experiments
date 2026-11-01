I’ll inspect the controller, service, and existing request-validation conventions, then implement the optional status filter and run the mandated offline Maven tests.

The endpoint now parses `status` strictly via the existing `Account.Status` enum, filters only after the existing visibility query, and relies on the project’s existing `IllegalArgumentException` → 400 mapping for invalid values. I’m running the full offline test suite now.

Implemented optional `status` filtering for `GET /api/accounts`:

- Accepts only `OPEN` or `CLOSED` (case-sensitive).
- Filters after existing visibility rules.
- Invalid values return 400 via existing exception handling.
- No parameter preserves current behavior.

`mvn -o -q test` could not run because the local Maven cache lacks the Spring Boot dependency descriptor and offline resolution failed.