Part 2 — protected admin APIs and request/response DTOs

Own these files (and only these, plus any narrowly necessary tests):
- sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/** (only the admin limits additions or a new limits controller)
- sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/** (new cart-rules controller if appropriate)
- sm-shop-model/src/main/java/com/salesmanager/shop/model/** (new limits/cart-rules DTOs only)

Add protected /api/v1/private endpoints following existing private API store resolution and authorization conventions. Validate atomically before mutating; return 200 and JSON values including nulls; map unknown/cross-store product to 404 and invalid values to 400.

Requirements from TASK.md:
- PUT /api/v1/private/product/{id}/limits with {"minPerCart": 2, "maxPerCart": 6, "packSize": 2} sets the product's limits and returns HTTP 200 with them; GET returns them. Each is optional (null when not set); setting all three to null removes the limits. An unknown product, or one from another store, gives HTTP 404 Not Found.
- PUT /api/v1/private/cart-rules with {"maxLines": 10, "maxUnits": 50} sets the store's caps (each optional, null for none) and returns HTTP 200 with them; GET returns them.
- Every limit and cap is a whole number of at least 1. minPerCart may not be more than maxPerCart, and maxPerCart may not be less than packSize. Anything else gives HTTP 400 Bad Request and keeps the old values.

Other parts provide/use:
- Part 1 provides ProductService/MerchantStoreService and entity getters/setters for persistence.
- Part 3 consumes the resulting persisted values; do not edit cart facade, mapper, or cart DTO files owned there.
