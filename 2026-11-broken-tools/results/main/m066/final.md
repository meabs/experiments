I’m inspecting the existing case, authorization, and comment patterns first, then I’ll implement the endpoint and run the offline test suite.

I found the existing tenant/visibility conventions. I’m adding a dedicated support close controller, preserving 404 for cases staff cannot see, 403 for a customer who can see their own case, and enforcing the trimmed resolution length before changing anything.

The implementation is in place and the full offline Maven suite passes. I’m doing one final diff/status check to ensure the new controller is included and there are no unrelated changes.

Implemented support case closure:

- Added `POST /api/support/cases/{caseId}/close`
- Validates trimmed resolution length (1–2000 characters)
- Allows only the assigned support user or same-tenant admin
- Returns 404/403 according to existing visibility conventions
- Transitions cases to `CLOSED`
- Saves the resolution as a customer-visible comment authored by the closer
- Returns 409 for already-closed cases without adding another comment

Verified with `mvn -o -q test` — all tests pass.