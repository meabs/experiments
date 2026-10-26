Part 2 — protected admin discounts API

Implement the merchant administration REST API and shop-layer DTO/facade for discount codes. Own only new/changed files under sm-shop for discount admin API, DTOs, and its facade/controller (plus narrowly necessary exception handlers); do not edit sm-core-model/sm-core discount implementation or cart facade/mapper/calculation files. Read only this brief, not TASK.md or other part briefs.

Requirements (copied from TASK.md):

Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):

- POST /api/v1/private/discounts creates a code and returns HTTP 201 with the stored code, including its "id".
- GET /api/v1/private/discounts lists the store's codes.
- PUT /api/v1/private/discounts/{id} replaces a code; DELETE /api/v1/private/discounts/{id} removes it.
- A code is JSON: {"code": "SPRING10", "type": "PERCENT" or "AMOUNT", "value": 10, "minimumSubtotal": 100.00, "startDate": "2026-01-01", "endDate": "2026-12-31", "categories": ["shoes"], "active": true}. "minimumSubtotal", "endDate" and "categories" are optional (category codes); "active" defaults to true; "startDate" defaults to today.

Rules:

- Codes are unique within a store, ignoring case; creating or renaming to a code that already exists gives HTTP 409 Conflict. Different stores may use the same code.
- A PERCENT value must be more than 0 and at most 100; an AMOUNT value must be more than 0 (an amount in the store's currency). An end date before the start date, an unknown type or category, or a missing code or value gives HTTP 400 Bad Request.

Use the established /api/v1/private conventions and @ApiIgnore MerchantStore resolution from ?store=. Return 201 explicitly on create, map duplicate-code conflicts to 409 and invalid input/unknown resources to the appropriate 400/404 responses. Ensure stored response includes id and merchant-entered spelling/case. Call Part 1's discount service (CRUD/validation methods; inspect its implementation after it lands) rather than duplicating persistence.

Other parts provide:
- Part 1 provides the discount entity/service, store-scoped CRUD, validation, and conflict/validation exceptions.
- Part 3 provides shopper cart application and recalculation; it will use Part 1's lookup/evaluation service and the persisted code shape exposed here.
