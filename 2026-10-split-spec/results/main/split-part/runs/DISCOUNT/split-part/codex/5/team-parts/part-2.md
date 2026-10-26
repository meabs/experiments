Part 2 – protected administration API

Implement the private discount REST API. Own new/changed files under sm-shop/src/main/java/.../store/api/v1 (discount package/controller), shop discount request/response model/DTO packages, and only API-specific configuration. Follow the same protection and MerchantStore resolver conventions as existing /api/v1/private endpoints; do not edit core discount persistence/service or cart files.

Requirements (exact task wording):
- Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):
- POST /api/v1/private/discounts creates a code and returns HTTP 201 with the stored code, including its "id".
- GET /api/v1/private/discounts lists the store's codes.
- PUT /api/v1/private/discounts/{id} replaces a code; DELETE /api/v1/private/discounts/{id} removes it.
- A code is JSON: {"code": "SPRING10", "type": "PERCENT" or "AMOUNT", "value": 10, "minimumSubtotal": 100.00, "startDate": "2026-01-01", "endDate": "2026-12-31", "categories": ["shoes"], "active": true}. "minimumSubtotal", "endDate" and "categories" are optional (category codes); "active" defaults to true; "startDate" defaults to today.
- Codes are unique within a store, ignoring case; creating or renaming to a code that already exists gives HTTP 409 Conflict. Different stores may use the same code.
- A PERCENT value must be more than 0 and at most 100; an AMOUNT value must be more than 0 (an amount in the store's currency). An end date before the start date, an unknown type or category, or a missing code or value gives HTTP 400 Bad Request.

Use HTTP 400/409/404 appropriately, return persisted id and merchant casing, and bind ?store= through the normal MerchantStore argument resolver/authentication.

Other parts provide/consume: Part 1 supplies the discount model and service CRUD/validation methods. Part 3 is independent and consumes the same service.
