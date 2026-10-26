Part 1 — persistence and domain services

Implement the storage/domain support for product purchase limits and per-store cart caps. Read TASK.md first. Own only files under sm-core-model/src/main/java/com/salesmanager/core/model (including Product and MerchantStore) and sm-core/src/main/java/com/salesmanager/core/business/repositories plus services needed for this feature; add focused repository/service classes in those modules as needed. Do not edit sm-shop API/controller/populator files owned by parts 2/3.

Provide stable methods that the other parts can call, preferably a product-limit API on ProductService (get/update by product id and MerchantStore) and a cart-rule API on MerchantStore/merchant service (get/update by store), with validation that values are positive whole numbers and min <= max and max >= packSize. Unknown or cross-store products must be distinguishable as absent. Keep persistence compatible with the existing JPA schema conventions and ensure clearing all values with null works.

Part 2 relies on these domain methods and model accessors to implement the protected admin endpoints. Part 3 relies on the same accessors/services to validate cart mutations and compute warnings.
