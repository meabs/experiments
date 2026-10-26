Part 2 — private administration API

Implement the protected v1 private REST endpoints for configuring product limits and store cart rules. Own only the new/modified admin API controller(s), request/response DTOs specific to that API, and API-layer validation/error handling needed for these endpoints. Do not edit persistence/service internals owned by Part 1 or cart mutation/populator code owned by Part 3.

Requirements from TASK.md that apply:

Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):

- PUT /api/v1/private/product/{id}/limits with {"minPerCart": 2, "maxPerCart": 6, "packSize": 2} sets the product's limits and returns HTTP 200 with them; GET returns them. Each is optional (null when not set); setting all three to null removes the limits. An unknown product, or one from another store, gives HTTP 404 Not Found.
- PUT /api/v1/private/cart-rules with {"maxLines": 10, "maxUnits": 50} sets the store's caps (each optional, null for none) and returns HTTP 200 with them; GET returns them.
- Every limit and cap is a whole number of at least 1. minPerCart may not be more than maxPerCart, and maxPerCart may not be less than packSize. Anything else gives HTTP 400 Bad Request and keeps the old values.

Use the same store resolution/security conventions as existing private endpoints. Return the configured values as JSON with the exact field names above and appropriate 200/400/404 statuses. Validation must happen before saving so invalid updates leave old values untouched.

Files owned: controller classes under sm-shop/src/main/java/com/salesmanager/shop/store/api/v1 (and narrowly related API DTO/exception files), plus API tests if useful. Do not modify shared model/service files or cart files owned by the other parts.

Other parts rely on: Part 1's ProductLimits, CartRules, and persistence service methods. The API must call those methods and pass the resolved MerchantStore, and should expose their values without inventing a second storage path.
