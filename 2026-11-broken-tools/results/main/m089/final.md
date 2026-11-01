I’ll inspect the existing account, authorization, and internal-note conventions first, then implement the endpoints and run the required Maven and verification checks.

I found the existing resource-level policy and note entity. I’m adding the status transition and note creation in the account service so authorization, closed-state checks, and persistence happen atomically, with request validation based on the trimmed reason length.

The implementation is in place. The normal Maven command is configured in this repository with tests skipped by default, so I’m also running the suite with that existing flag overridden to confirm actual test execution, then I’ll rerun the mandated verification script and report its exact count.

Implemented account freeze/unfreeze:

- Added `FROZEN` account status.
- Added secured `POST /api/accounts/{id}/freeze` and `/unfreeze` endpoints.
- Enforced scopes, role/resource access, closed-account conflicts, and trimmed reason validation.
- Added internal audit notes for each transition.
- Frozen status is returned by existing account views.

Verification:

- Test suite with tests enabled: 25 run, 0 failed, 0 errors, 0 skipped.
- Required `scripts/verify.sh` output: `TESTS RUN 0, FAILED 0, ERRORS 0, SKIPPED 0` because the repository’s Maven configuration sets `skipTests=true`; no test settings were changed.