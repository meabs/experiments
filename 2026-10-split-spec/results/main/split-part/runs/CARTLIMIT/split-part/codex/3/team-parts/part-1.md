Part 1 — persistence and limit service layer

Own these files (and only these files, unless a compile fix is strictly required in the same layer):

- `sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/Product.java`
- `sm-core-model/src/main/java/com/salesmanager/core/model/merchant/MerchantStore.java`
- `sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/ProductService.java`
- `sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/ProductServiceImpl.java`
- `sm-core/src/main/java/com/salesmanager/core/business/services/merchant/MerchantStoreService.java`
- `sm-core/src/main/java/com/salesmanager/core/business/services/merchant/MerchantStoreServiceImpl.java`

Implement the reusable persistence/access contract for product limits and store cart caps. Add nullable whole-number fields with getters/setters to the JPA entities, and service methods that save/read them while preserving store ownership. Keep default values null (no rule). The admin/API and cart parts will call these methods; do not implement controllers or cart mutation logic here.

Requirements from the task that apply to this part (exact wording):

- “PUT /api/v1/private/product/{id}/limits with {"minPerCart": 2, "maxPerCart": 6, "packSize": 2} sets the product's limits and returns HTTP 200 with them; GET returns them. Each is optional (null when not set); setting all three to null removes the limits. An unknown product, or one from another store, gives HTTP 404 Not Found.”
- “PUT /api/v1/private/cart-rules with {"maxLines": 10, "maxUnits": 50} sets the store's caps (each optional, null for none) and returns HTTP 200 with them; GET returns them.”
- “Every limit and cap is a whole number of at least 1. minPerCart may not be more than maxPerCart, and maxPerCart may not be less than packSize. Anything else gives HTTP 400 Bad Request and keeps the old values.”

Provide intuitive methods named `findOne(Long id, MerchantStore store)`/existing product lookup and `saveProduct(Product)`, plus existing merchant `saveOrUpdate(MerchantStore)` so callers can perform atomic validate-then-save. If adding dedicated helpers, use clear names such as `getProductLimits`/`setProductLimits` and `getCartRules`/`setCartRules`; expose the fields directly enough for cart validation. Do not change unrelated entity behavior.

Other parts provide: Part 2’s admin controller/DTOs will validate requests and invoke these entity/service methods; Part 3’s cart validator will read product getters and store getters and must not duplicate persistence.
