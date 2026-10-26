Part 1 — core model and persistence/service contracts

Own these files (and only these areas):
- `sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/Product.java`
- `sm-core-model/src/main/java/com/salesmanager/core/model/merchant/MerchantStore.java`
- New core-model limit/rule value/entity classes under the corresponding `com.salesmanager.core.model...` packages.
- New/changed repositories and services under `sm-core/src/main/java/com/salesmanager/core/business/repositories` and `.../services` for product limits and store cart rules.

Requirements (exact task wording):
- PUT /api/v1/private/product/{id}/limits with {"minPerCart": 2, "maxPerCart": 6, "packSize": 2} sets the product's limits and returns HTTP 200 with them; GET returns them. Each is optional (null when not set); setting all three to null removes the limits. An unknown product, or one from another store, gives HTTP 404 Not Found.
- PUT /api/v1/private/cart-rules with {"maxLines": 10, "maxUnits": 50} sets the store's caps (each optional, null for none) and returns HTTP 200 with them; GET returns them.
- Every limit and cap is a whole number of at least 1. minPerCart may not be more than maxPerCart, and maxPerCart may not be less than packSize. Anything else gives HTTP 400 Bad Request and keeps the old values.

Provide stable methods/classes for other parts, at minimum a product-limit service that can get/update by product id and store, a store-rule service that can get/update by store, and immutable/readable DTO-style objects exposing `getMinPerCart`, `getMaxPerCart`, `getPackSize`, `getMaxLines`, and `getMaxUnits`. Preserve old values on validation failure and enforce store ownership.

Part 2 will call these services from the protected admin API. Part 3 will call them while validating cart mutations and computing warnings.
