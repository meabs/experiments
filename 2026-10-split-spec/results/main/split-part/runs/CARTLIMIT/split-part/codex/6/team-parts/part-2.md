Part 2 — protected admin limits API

Scope and owned files

- Own the new or modified API/controller and request/response DTO files under `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/` and `sm-shop-model/src/main/java/com/salesmanager/shop/model/` needed for the two admin resources.
- You may add focused validation/exception handling classes in the shop API layer, but do not edit Product/MerchantStore domain classes or cart facade/mapper/model files owned by Parts 1 and 3.

Requirements from TASK.md that apply to this part (exact wording)

- “Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):”
- “PUT /api/v1/private/product/{id}/limits with {"minPerCart": 2, "maxPerCart": 6, "packSize": 2} sets the product's limits and returns HTTP 200 with them; GET returns them. Each is optional (null when not set); setting all three to null removes the limits. An unknown product, or one from another store, gives HTTP 404 Not Found.”
- “PUT /api/v1/private/cart-rules with {"maxLines": 10, "maxUnits": 50} sets the store's caps (each optional, null for none) and returns HTTP 200 with them; GET returns them.”
- “Every limit and cap is a whole number of at least 1. minPerCart may not be more than maxPerCart, and maxPerCart may not be less than packSize. Anything else gives HTTP 400 Bad Request and keeps the old values.”

Implementation contract for other parts

- Consume Part 1’s nullable Product getters/setters (`getMinPerCart`, `getMaxPerCart`, `getPackSize`) and MerchantStore getters/setters (`getMaxLines`, `getMaxUnits`) and existing ProductService/MerchantStoreService persistence.
- Return JSON fields exactly `minPerCart`, `maxPerCart`, `packSize` and `maxLines`, `maxUnits`, including nulls.
- Validate the complete proposed state before mutating or saving, so every invalid whole-number/relationship request responds 400 and leaves old values unchanged. Enforce product lookup by id plus the supplied store and return 404 for missing/cross-store products.
- Match existing private endpoint conventions for store resolution/authentication and HTTP response handling.
