I’m reviewing the existing case, security, and API patterns first, then I’ll implement the close flow and run the mandated offline test suite.

I found the existing case model has no mutation endpoint or comment constructor, so I’m adding a dedicated support controller, a guarded state transition on the entity, and a persisted customer-visible comment in the same transaction. Validation will be applied to the trimmed resolution text.

Implemented support-case closure.

Changes:
- Added `POST /api/support/cases/{caseId}/close`.
- Enforced tenant, assignee/admin, role, and scope checks.
- Added trimmed 1–2000 character resolution validation.
- Cases transition to `CLOSED`; repeated closure returns 409.
- Resolutions are saved as customer-visible comments authored by the closer.
- Added entity support for case closing and comment creation.

Verification: `mvn -o -q test` passes all existing tests.