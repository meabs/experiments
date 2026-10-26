# Part 1 — Core limit and store-rule model/services

## Ownership

Own only core/domain and core-service files needed to persist and retrieve limits. Likely files are under `sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/`, `sm-core-model/src/main/java/com/salesmanager/core/model/merchant/`, and `sm-core/src/main/java/com/salesmanager/core/business/services/` (plus narrowly necessary core repository/configuration files). Do not edit `sm-shop`, `sm-shop-model`, or controller/cart files owned by other parts.

## Requirements (exact task wording)

Merchants need purchase limits: some products sell only in packs, some only a few per customer, and the store wants to cap the size of any cart. Add per-product limits and store-wide cart caps, enforce them whenever a cart changes, and show shoppers which rules a cart breaks.

Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):

- PUT /api/v1/private/product/{id}/limits with {"minPerCart": 2, "maxPerCart": 6, "packSize": 2} sets the product's limits and returns HTTP 200 with them; GET returns them. Each is optional (null when not set); setting all three to null removes the limits. An unknown product, or one from another store, gives HTTP 404 Not Found.
- PUT /api/v1/private/cart-rules with {"maxLines": 10, "maxUnits": 50} sets the store's caps (each optional, null for none) and returns HTTP 200 with them; GET returns them.
- Every limit and cap is a whole number of at least 1. minPerCart may not be more than maxPerCart, and maxPerCart may not be less than packSize. Anything else gives HTTP 400 Bad Request and keeps the old values.

In the cart (POST /api/v1/cart, PUT /api/v1/cart/{code} and POST /api/v1/cart/{code}/multi):

- A line's quantity must be at least the product's minPerCart, at most its maxPerCart, and a multiple of its packSize. Removing a line (quantity 0) is always allowed.
- A cart may hold at most maxLines different products and maxUnits units in all.
- A change that breaks a rule is refused with HTTP 400 Bad Request and the rule's name as the error's "errorCode": MIN_PER_CART, MAX_PER_CART, PACK_SIZE, MAX_LINES or MAX_UNITS. A refused change changes nothing in the cart, including the other lines of a multi request.
- Product limits are checked for the lines a change adds or changes. The store's caps are checked only when a change adds a line (maxLines) or adds units (maxUnits). So a cart that breaks a rule set later can still be changed to fix it.
- The cart, whenever it is returned, has "limitWarnings": a list of the rules it breaks now, as {"sku": "...", "rule": "MAX_PER_CART"} (with "sku": null for MAX_LINES and MAX_UNITS); an empty list when it breaks none.

## Contracts for other parts

Expose stable getters/setters on `Product` named `getMinPerCart()`, `setMinPerCart(Integer)`, `getMaxPerCart()`, `setMaxPerCart(Integer)`, `getPackSize()`, `setPackSize(Integer)` (nullable). Expose `MerchantStore` getters/setters named `getMaxLines()`, `setMaxLines(Integer)`, `getMaxUnits()`, `setMaxUnits(Integer)` (nullable), persisted with the existing JPA model. Keep normal `ProductService`/`MerchantStoreService` save/update semantics so the admin controller can retrieve a store-scoped product with `ProductService.findOne/retrieveById` and persist via `update`/`saveProduct`, and persist store caps via `MerchantStoreService.saveOrUpdate`.

If useful to avoid duplicated validation, provide a core service/helper with an obvious public method for validating a proposed cart snapshot, but do not change shop-layer files. Other parts will call the model getters directly unless you document a helper in your completion message.

Run focused Maven compilation/tests for the modules you touch.
