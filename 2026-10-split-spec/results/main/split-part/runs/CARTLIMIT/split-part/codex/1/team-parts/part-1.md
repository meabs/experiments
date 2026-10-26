Part 1 owns the data model, persistence/service layer, and protected admin endpoints for product limits and store cart rules.

Files you own (create or modify only these, plus narrowly necessary package-local tests):
- sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/Product.java (or the concrete product model actually persisted)
- sm-core-model/src/main/java/com/salesmanager/core/model/merchant/MerchantStore.java
- sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/** (only limit-related additions)
- sm-core/src/main/java/com/salesmanager/core/business/repositories/catalog/product/** (only limit-related additions)
- sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/** (only the new limits endpoint)
- sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/store/** (only the new cart-rules endpoint)
- sm-shop/src/main/java/com/salesmanager/shop/model/** (DTOs for the two admin payloads/responses)

Requirements (exact task wording):
- PUT /api/v1/private/product/{id}/limits with {"minPerCart": 2, "maxPerCart": 6, "packSize": 2} sets the product's limits and returns HTTP 200 with them; GET returns them. Each is optional (null when not set); setting all three to null removes the limits. An unknown product, or one from another store, gives HTTP 404 Not Found.
- PUT /api/v1/private/cart-rules with {"maxLines": 10, "maxUnits": 50} sets the store's caps (each optional, null for none) and returns HTTP 200 with them; GET returns them.
- Every limit and cap is a whole number of at least 1. minPerCart may not be more than maxPerCart, and maxPerCart may not be less than packSize. Anything else gives HTTP 400 Bad Request and keeps the old values.

Provide to other parts:
- Product getters/setters or a ProductLimit value object for minPerCart, maxPerCart, packSize, exposed through ProductService (or equivalent) with store-scoped lookup/update.
- A store-scoped CartRules value/service with get/set maxLines and maxUnits.
- Validation exceptions/DTOs that let the cart layer identify invalid admin input without partially saving.
