I’ll inspect the existing account, authorization, and note patterns first, then implement the two endpoints and run the offline test suite, checking the exact test counts.

I found the existing resource-level access pattern: visibility is resolved first (preserving 404 for inaccessible accounts), then role-specific mutations are checked, with state conflicts mapped to 409. I’m extending that pattern and adding persisted internal notes for each action.

The implementation is in place: `FROZEN` is now a persisted account status; freeze/unfreeze enforce scope, tenant visibility, support/admin rules, and closed-account conflicts; each successful action writes an internal note with the actor and (for freezes) trimmed reason. I’m doing the final offline test verification now.

Implemented account freezing and unfreezing.

- Added `FROZEN` account status.
- Added scoped freeze/unfreeze endpoints with validation and authorization rules.
- Enforced closed-account conflicts and support/admin permissions.
- Added internal audit notes for every action, including freeze reasons.
- Preserved existing account response shape.

Tests: `25` run, `0` failures, `0` errors, `0` skipped via `mvn -o -q test`.