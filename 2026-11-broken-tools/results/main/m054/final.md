I’ll inspect the existing account-list endpoint, its validation conventions, and tests, then implement the optional status filter and run the mandated verification.

The existing endpoint computes visibility in `AccountService` and maps results in `AccountController`. I’ll parse `status` strictly as the existing `Account.Status` enum, then filter only after visibility has been established so access rules remain unchanged; invalid values will use the existing 400 handling.

The implementation is in place and the Maven test run completed successfully. I’m running the repository’s required `scripts/verify.sh` now to capture the authoritative test counts.

Implemented optional `status` filtering for `GET /api/accounts`.

- Accepts only `OPEN` or `CLOSED` (case-sensitive).
- Invalid values return `400`.
- Visibility rules remain unchanged; filtering occurs after authorization.

Verification: `TESTS RUN 9, FAILED 0, ERRORS 0, SKIPPED 0`.