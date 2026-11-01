I’ll inspect the existing account, authorization, and note-handling conventions, then implement the two endpoints and run the mandated test/verification commands.

I found the existing resource-level policy and internal-note entities. I’m adding the state transition in the account service so authorization, closed-state conflicts, status updates, and note creation happen transactionally.

The implementation is in place and the full verification suite currently passes (25 tests). I’m doing one additional review of edge-case ordering—scope, visibility, role checks, and closed-state conflicts—before finalizing.

Implemented account freezing/unfreezing:

- Added `FROZEN` account status.
- Added scoped freeze/unfreeze endpoints with role and tenant checks.
- Added reason validation (trimmed length 1–500).
- Added closed-account conflicts.
- Added internal audit notes for each action.
- Preserved existing account response shape.

Verification: `TESTS RUN 25, FAILED 0, ERRORS 0, SKIPPED 0`.