# Part 2 — merchant discount DTO and protected CRUD API

## Scope and owned files

Own all new or modified files under `sm-shop-model/src/main/java/com/salesmanager/shop/model/discount/` and all new or modified discount controller/API files under `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/discount/` (plus narrowly necessary API exception/mapper files). Do not edit core discount persistence/service files or cart/order-total files owned by the other parts.

Add request/response model(s) representing every JSON field exactly, with id in stored responses, defaults, and validation annotations as appropriate. Add a protected controller consistent with existing `/api/v1/private` APIs and MerchantStore resolution via `?store=`. Translate validation failures to 400, duplicate code conflicts to 409, and successful create to 201. PUT replaces the complete code and DELETE removes it; GET lists only the selected store.

## Exact task requirements applying to this part

Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):

- POST /api/v1/private/discounts creates a code and returns HTTP 201 with the stored code, including its "id".
- GET /api/v1/private/discounts lists the store's codes.
- PUT /api/v1/private/discounts/{id} replaces a code; DELETE /api/v1/private/discounts/{id} removes it.
- A code is JSON: {"code": "SPRING10", "type": "PERCENT" or "AMOUNT", "value": 10, "minimumSubtotal": 100.00, "startDate": "2026-01-01", "endDate": "2026-12-31", "categories": ["shoes"], "active": true}. "minimumSubtotal", "endDate" and "categories" are optional (category codes); "active" defaults to true; "startDate" defaults to today.

Rules:

- Codes are unique within a store, ignoring case; creating or renaming to a code that already exists gives HTTP 409 Conflict. Different stores may use the same code.
- A PERCENT value must be more than 0 and at most 100; an AMOUNT value must be more than 0 (an amount in the store's currency). An end date before the start date, an unknown type or category, or a missing code or value gives HTTP 400 Bad Request.

## What other parts provide / rely on

Part 1 provides `DiscountService`/`DiscountServiceImpl` CRUD methods, store-scoped duplicate detection, and validation exceptions. Use its entity/model fields and return persisted ids. Part 3 relies on the API leaving cart endpoints untouched and on the same service storing the merchant-written code casing.
