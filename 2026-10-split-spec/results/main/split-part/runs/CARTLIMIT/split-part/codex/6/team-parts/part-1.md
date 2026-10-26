Part 1 — domain model and persistence

Scope and owned files

- Own the core domain/persistence files under `sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/` and `.../merchant/` that hold Product and MerchantStore state.
- Own any core service/repository files under `sm-core/src/main/java/com/salesmanager/core/business/` needed to load/save products or stores for the limits (only if the existing generic services cannot do it).
- Do not edit controllers, cart facades, cart mappers, or API DTO/controller files owned by the other parts.

Requirements from TASK.md that apply to this part (exact wording)

- “PUT /api/v1/private/product/{id}/limits with {"minPerCart": 2, "maxPerCart": 6, "packSize": 2} sets the product's limits and returns HTTP 200 with them; GET returns them. Each is optional (null when not set); setting all three to null removes the limits. An unknown product, or one from another store, gives HTTP 404 Not Found.”
- “PUT /api/v1/private/cart-rules with {"maxLines": 10, "maxUnits": 50} sets the store's caps (each optional, null for none) and returns HTTP 200 with them; GET returns them.”
- “Every limit and cap is a whole number of at least 1. minPerCart may not be more than maxPerCart, and maxPerCart may not be less than packSize. Anything else gives HTTP 400 Bad Request and keeps the old values.”

Implementation contract for other parts

- Product must expose nullable Integer getters/setters named `getMinPerCart`/`setMinPerCart`, `getMaxPerCart`/`setMaxPerCart`, and `getPackSize`/`setPackSize`.
- MerchantStore must expose nullable Integer getters/setters named `getMaxLines`/`setMaxLines` and `getMaxUnits`/`setMaxUnits`.
- Persist these values as nullable columns using the project’s normal JPA conventions. Existing ProductService and MerchantStoreService should be usable by the API part to retrieve/save entities and enforce store ownership; add narrowly scoped service methods only if required.
- Preserve null as “not configured”; do not silently coerce null to a default.
