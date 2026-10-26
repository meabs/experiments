Part 1 — limits and store-rule persistence

Own these files (and only these, plus any narrowly necessary tests):
- sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/Product.java
- sm-core-model/src/main/java/com/salesmanager/core/model/merchant/MerchantStore.java
- sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/**
- sm-core/src/main/java/com/salesmanager/core/business/services/merchant/**
- any new persistence/model files under sm-core-model or service/repository files under sm-core needed to persist the values

Implement the durable product fields minPerCart, maxPerCart, packSize and store-wide maxLines, maxUnits, with getters/setters and service access suitable for the API and cart code. Preserve null as “not set”. Ensure normal entity save/update persists them.

Requirements from TASK.md:
- PUT /api/v1/private/product/{id}/limits with {"minPerCart": 2, "maxPerCart": 6, "packSize": 2} sets the product's limits and returns HTTP 200 with them; GET returns them. Each is optional (null when not set); setting all three to null removes the limits. An unknown product, or one from another store, gives HTTP 404 Not Found.
- PUT /api/v1/private/cart-rules with {"maxLines": 10, "maxUnits": 50} sets the store's caps (each optional, null for none) and returns HTTP 200 with them; GET returns them.
- Every limit and cap is a whole number of at least 1. minPerCart may not be more than maxPerCart, and maxPerCart may not be less than packSize. Anything else gives HTTP 400 Bad Request and keeps the old values.

Other parts provide/use:
- Part 2 admin controllers call ProductService / MerchantStoreService and entity getters/setters (or clearly named methods you expose).
- Part 3 cart enforcement reads product getMinPerCart/getMaxPerCart/getPackSize and store getMaxLines/getMaxUnits.
