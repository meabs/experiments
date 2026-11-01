I’ll inspect the account-list endpoint and its tests, then add the optional status validation/filter while preserving existing authorization behavior. I’ll run the mandated offline Maven test suite afterward.

The endpoint currently gets the caller-visible accounts from `AccountService` and maps them in `AccountController`; I’ll validate the raw query value there (case-sensitive via the existing `Account.Status` enum) and filter only after visibility has been applied. Invalid values will flow through the project’s existing `IllegalArgumentException`→400 handler.

The code change is in place and limited to the list endpoint: absent `status` preserves the old result, while `OPEN`/`CLOSED` filter the already-authorized list. I also confirmed the diff has no whitespace errors. The required Maven command is currently blocked because the local cache lacks the Spring Boot 3.5.6 artifact descriptor and offline Maven cannot resolve it.

Implemented optional status filtering for `GET /api/accounts`:

- Accepts only exact `OPEN` or `CLOSED`.
- Filters after applying existing visibility rules.
- Omitting `status` preserves existing behavior.
- Invalid values return 400 via the existing exception handler.

Validation: `git diff --check` passed. `mvn -o -q test` could not run because the local Maven cache lacks the Spring Boot 3.5.6 descriptor.