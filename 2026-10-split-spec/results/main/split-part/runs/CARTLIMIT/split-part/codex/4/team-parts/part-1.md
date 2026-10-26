Part 1 — limits data model and services

Implement the persistent/domain support for product purchase limits and store-wide cart caps. Own only new or modified core/model/service/repository/migration files needed to represent and retrieve these settings (including DTOs used by the APIs), and any narrowly scoped exception/value types. Do not edit REST controllers or cart mutation/facade code owned by Parts 2 and 3.

Requirements from TASK.md that apply:

- Merchants need purchase limits: some products sell only in packs, some only a few per customer, and the store wants to cap the size of any cart. Add per-product limits and store-wide cart caps, enforce them whenever a cart changes, and show shoppers which rules a cart breaks.
- Every limit and cap is a whole number of at least 1. minPerCart may not be more than maxPerCart, and maxPerCart may not be less than packSize. Anything else gives HTTP 400 Bad Request and keeps the old values.
- Each product limit is optional (null when not set); setting all three to null removes the limits.
- Store caps are each optional, null for none.

Provide stable class/method names for other parts, preferably a ProductLimits value/DTO with getMinPerCart(), getMaxPerCart(), getPackSize(), a CartRules value/DTO with getMaxLines(), getMaxUnits(), and a service such as PurchaseLimitsService with product lookup/update and store rules lookup/update methods. Ensure product/store ownership can be checked by callers and persistence survives normal application restarts.

Files owned: the relevant sm-core-model/sm-shop-model entity and DTO files, sm-core service/repository/DAO files, and schema/migration/config files required for persistence. Do not touch files assigned in Parts 2 or 3.

Other parts rely on: ProductLimits, CartRules, and the service methods you expose; cart code will use these to validate quantities and compute warnings, while the admin API will use them to read/write settings and distinguish unknown/cross-store products.
