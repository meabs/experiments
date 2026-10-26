Part 2 — admin API and shop DTOs

Implement the protected v1 admin REST API and request/response models. Own only new/modified files under `sm-shop-model/src/main/java/com/salesmanager/shop/model/discount/**` and `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/discount/**` (plus a mapper in a discount-specific package if needed). Do not edit core discount files or cart files. Follow existing private API conventions and resolve the store from the `?store=` query parameter and authenticated context.

Requirements (exact task wording):

- Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):
- POST /api/v1/private/discounts creates a code and returns HTTP 201 with the stored code, including its "id".
- GET /api/v1/private/discounts lists the store's codes.
- PUT /api/v1/private/discounts/{id} replaces a code; DELETE /api/v1/private/discounts/{id} removes it.
- A code is JSON: {"code": "SPRING10", "type": "PERCENT" or "AMOUNT", "value": 10, "minimumSubtotal": 100.00, "startDate": "2026-01-01", "endDate": "2026-12-31", "categories": ["shoes"], "active": true}. "minimumSubtotal", "endDate" and "categories" are optional (category codes); "active" defaults to true; "startDate" defaults to today.
- Codes are unique within a store, ignoring case; creating or renaming to a code that already exists gives HTTP 409 Conflict. Different stores may use the same code.
- A PERCENT value must be more than 0 and at most 100; an AMOUNT value must be more than 0 (an amount in the store's currency). An end date before the start date, an unknown type or category, or a missing code or value gives HTTP 400 Bad Request.

Use the service API from Part 1. Return 400 for validation failures, 409 for duplicate codes, and appropriate not-found responses for missing ids. The JSON response must expose the stored `id` and merchant-entered fields. Part 3 supplies shopper/cart behavior and will rely on the same service's case-insensitive lookup.
