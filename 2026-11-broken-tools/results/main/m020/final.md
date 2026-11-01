I’ll inspect the existing account, authorization, and note patterns, then implement the endpoints and run the mandated offline test suite.

The account model now supports `FROZEN`; I’ve added scoped freeze/unfreeze routes, role/resource checks, closed-account conflicts, and internal audit notes with the acting user and freeze reason. I’m running the full offline suite now to catch integration issues.

The offline suite passes. I also cleaned up an import duplication found during review; the implementation remains limited to the account status, controller, service, and note entity changes.

Implemented account freeze/unfreeze functionality:

- Added `FROZEN` account status.
- Added scoped `POST /api/accounts/{id}/freeze` and `/unfreeze` endpoints.
- Enforced validation, tenant visibility, role permissions, and closed-account conflicts.
- Added internal audit notes for every freeze/unfreeze.
- Freeze notes include the trimmed reason and acting user.

`mvn -o -q test` passes.