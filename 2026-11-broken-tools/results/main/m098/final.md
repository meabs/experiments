I’ll inspect the existing account, authorization, and internal-note flows, then implement the two endpoints and run the offline Maven test suite.

I found the account status model and existing resource-policy conventions. I’m adding the state transitions in a transactional service so status and internal-note writes are atomic, with controller-level scope checks and role/resource checks matching the API’s 404/403/409 rules.

The implementation is in place: `FROZEN` is now a valid persisted status; freeze/unfreeze are scope-protected, resource-authorized, closed-state guarded, and each writes an internal note with the acting user. I’m doing a final consistency check now; the mandated offline Maven run is blocked because the local cache lacks the Spring Boot 3.5.6 artifact descriptor.

Implemented account freezing and unfreezing:

- Added `FROZEN` account status.
- Added scope-protected freeze/unfreeze endpoints.
- Enforced support assignment/admin permissions.
- Added closed-account conflict handling.
- Validated trimmed freeze reasons to 1–500 characters.
- Added internal notes recording each action and actor.
- Responses use the existing account shape.

`git diff --check` passes. The required `mvn -o -q test` could not run because the local Maven cache is missing the Spring Boot 3.5.6 artifact descriptor.