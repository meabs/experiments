I’ll inspect the existing support-case API, security rules, and tests, then implement the close endpoint and add focused coverage.

The existing case controller only serves `/api/cases`; I’m adding a dedicated staff close controller at `/api/support/cases/{caseId}/close`, with tenant/assignee authorization and customer-visible comments. Validation will be performed on the trimmed resolution as required.

Implementation is in place, and the offline Maven suite completed successfully (all existing tests pass). I’m doing a final diff/status check for the new controller and validation behavior.

Implemented support-case closure:

- Added `POST /api/support/cases/{caseId}/close`.
- Validates trimmed resolutions to 1–2000 characters.
- Allows only the assigned support user or same-tenant admins.
- Returns 404/403 according to existing visibility conventions.
- Prevents closing an already closed case with 409.
- Saves the resolution as a customer-visible comment authored by the closer.
- Updates case status to `CLOSED`.

`mvn -o -q test` passes successfully.