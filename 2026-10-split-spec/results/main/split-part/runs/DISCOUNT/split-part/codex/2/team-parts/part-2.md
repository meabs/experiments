Part 2 — protected admin REST API

Own admin discount API/controller, request/response DTOs, mapping, and API tests under `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/**discount**`, `sm-shop/src/main/java/com/salesmanager/shop/store/controller/**discount**`, and `sm-shop-model/src/main/java/com/salesmanager/shop/model/**discount**` (plus narrowly related exception handling/config files if needed).

Implement endpoints protected like other `/api/v1/private` endpoints and scoped by `?store=`. Use the domain service from part 1. Return the stored code (including `id`) with HTTP 201 on create; list on GET; replace on PUT; remove on DELETE. Translate duplicate-code conflicts to 409 and invalid input/unknown category/type/date/value to 400, consistent with existing API conventions.

Exact task requirements for this part:

- POST /api/v1/private/discounts creates a code and returns HTTP 201 with the stored code, including its "id".
- GET /api/v1/private/discounts lists the store's codes.
- PUT /api/v1/private/discounts/{id} replaces a code; DELETE /api/v1/private/discounts/{id} removes it.
- A code is JSON: {"code": "SPRING10", "type": "PERCENT" or "AMOUNT", "value": 10, "minimumSubtotal": 100.00, "startDate": "2026-01-01", "endDate": "2026-12-31", "categories": ["shoes"], "active": true}. "minimumSubtotal", "endDate" and "categories" are optional (category codes); "active" defaults to true; "startDate" defaults to today.
- Codes are unique within a store, ignoring case; creating or renaming to a code that already exists gives HTTP 409 Conflict. Different stores may use the same code.
- A PERCENT value must be more than 0 and at most 100; an AMOUNT value must be more than 0 (an amount in the store's currency). An end date before the start date, an unknown type or category, or a missing code or value gives HTTP 400 Bad Request.

Part 1 provides the persistence/service methods and validation exceptions. Part 3 consumes the same service but does not depend on REST DTOs.
