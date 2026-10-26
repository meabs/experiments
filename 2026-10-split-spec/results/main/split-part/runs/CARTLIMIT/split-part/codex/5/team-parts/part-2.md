# Part 2 — Protected admin limits API and DTOs

## Ownership

Own only admin-facing shop model DTOs and API/controller files. Use `sm-shop-model/src/main/java/com/salesmanager/shop/model/...` for request/response DTOs and `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/...` (or an adjacent controller package) for the two endpoint groups. You may add narrowly scoped shop API exception handling needed to produce HTTP 400 with the requested `errorCode`, but do not edit cart facade/mapper/model files owned by Part 3 or core/domain files owned by Part 1.

## Requirements (exact task wording)

Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):

- PUT /api/v1/private/product/{id}/limits with {"minPerCart": 2, "maxPerCart": 6, "packSize": 2} sets the product's limits and returns HTTP 200 with them; GET returns them. Each is optional (null when not set); setting all three to null removes the limits. An unknown product, or one from another store, gives HTTP 404 Not Found.
- PUT /api/v1/private/cart-rules with {"maxLines": 10, "maxUnits": 50} sets the store's caps (each optional, null for none) and returns HTTP 200 with them; GET returns them.
- Every limit and cap is a whole number of at least 1. minPerCart may not be more than maxPerCart, and maxPerCart may not be less than packSize. Anything else gives HTTP 400 Bad Request and keeps the old values.

## API behavior/details

Use the same store resolution/security conventions as existing `/api/v1/private` product APIs and the `?store=` query parameter. Product lookup must be store-scoped; unknown or cross-store IDs are HTTP 404. PUT responses are HTTP 200 JSON containing exactly the nullable fields (`minPerCart`, `maxPerCart`, `packSize`) or (`maxLines`, `maxUnits`); GET returns the same shape. Validate the complete proposed set before mutating anything, including whole-number/at-least-1 checks and cross-field constraints, and retain old values on 400. Nulls are accepted and all-null product values remove product limits.

Use the core contracts from Part 1: `ProductService.findOne/retrieveById`, `ProductService.update/saveProduct`, `MerchantStoreService.saveOrUpdate`, and the nullable Product/MerchantStore getters/setters (`getMinPerCart`, `getMaxPerCart`, `getPackSize`, `getMaxLines`, `getMaxUnits`). A 400 must expose the invalid rule/request error in the existing API error shape; do not turn validation failures into 500s.

Run focused Maven compilation/tests for the modules you touch.
