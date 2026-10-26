Part 2 — protected admin REST API

Own these files (and only these areas):
- New API/controller classes under `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1` (use the existing private endpoint/security conventions).
- New request/response DTOs under `sm-shop-model/src/main/java/com/salesmanager/shop/model` (or the API module's established DTO package).
- API-layer exception/validation handling files only when needed for these endpoints.

Requirements (exact task wording):
- Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):
- PUT /api/v1/private/product/{id}/limits with {"minPerCart": 2, "maxPerCart": 6, "packSize": 2} sets the product's limits and returns HTTP 200 with them; GET returns them. Each is optional (null when not set); setting all three to null removes the limits. An unknown product, or one from another store, gives HTTP 404 Not Found.
- PUT /api/v1/private/cart-rules with {"maxLines": 10, "maxUnits": 50} sets the store's caps (each optional, null for none) and returns HTTP 200 with them; GET returns them.
- Every limit and cap is a whole number of at least 1. minPerCart may not be more than maxPerCart, and maxPerCart may not be less than packSize. Anything else gives HTTP 400 Bad Request and keeps the old values.

Use the Part 1 services and accessors (product-limit service and store-rule service). Ensure JSON nulls are accepted, all-null product payload removes limits, wrong/unknown product is 404, invalid payload is 400 without mutation, and endpoints return the exact fields and HTTP 200. Do not alter cart mutation behavior; Part 3 owns that.
