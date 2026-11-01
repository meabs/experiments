I’ll inspect the existing support-case API, security rules, and tests, then implement the close endpoint and add focused coverage before running the mandated Maven test command.

The existing conventions require hidden resources to return 404 across tenants, while same-tenant callers who can identify the case but lack the closing role get 403. I’ll implement that distinction, enforce the write scope, trim/validate the resolution, persist a customer-visible comment, and make closure state atomic within the transaction.

The mandated command completes successfully, but this repository’s POM sets `skipTests=true`, so Maven reports tests skipped. I’m running the same offline suite with that property overridden temporarily (without changing project settings) to verify the implementation and obtain the actual test count.

Implemented support-case closure:

- Added `POST /api/support/cases/{caseId}/close`
- Validates trimmed resolutions from 1–2000 characters
- Allows only the assigned support user or same-tenant admin
- Returns 404 across tenants and 403 for unauthorized same-tenant users
- Sets status to `CLOSED`
- Saves a customer-visible resolution comment with the closer as author
- Returns 409 for already-closed cases

Verification: 25 tests passed, 0 failed, 0 skipped when running with `-DskipTests=false`. The mandated command also succeeds, but the POM defaults to skipping tests.