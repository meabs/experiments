I’ll inspect the existing account, authorization, and note-handling conventions, then implement the two endpoints and run the offline test suite.

The account model now supports `FROZEN`; I’ve added scoped freeze/unfreeze routes, tenant/resource authorization, closed-account conflicts, trimmed reason validation, and internal audit notes. I’m running the existing suite now to catch integration or convention issues.

The offline suite passes (`mvn -o -q test`, exit 0). I also adjusted validation so the 1–500 limit is applied after trimming, as required—even when surrounding whitespace would otherwise push the raw JSON string over 500 characters.

Implemented account freeze/unfreeze support:

- Added `FROZEN` account status.
- Added scoped endpoints:
  - `POST /api/accounts/{accountId}/freeze`
  - `POST /api/accounts/{accountId}/unfreeze`
- Enforced admin/support authorization rules and closed-account conflicts.
- Added trimmed reason validation (1–500 characters).
- Added internal audit notes with author and freeze reason.
- Existing account response shape now reports `"status": "FROZEN"`.

Verified with `mvn -o -q test` successfully.