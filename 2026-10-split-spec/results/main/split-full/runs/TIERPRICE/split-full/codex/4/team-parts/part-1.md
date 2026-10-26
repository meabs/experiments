Part 1: quantity-tier domain model and persistence/service support.

Own these files (and any new files in the same packages needed for this part):
- sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/Product.java
- new core-model tier entity/DTO files under com.salesmanager.core.model.catalog.product
- sm-core/src/main/java/com/salesmanager/core/business/repositories/catalog/product/* (only tier-related repository additions/new repository)
- sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/* (only tier-related service interface/implementation additions)

Implement a per-product tier representation persisted with the product/store relationship, with minQuantity and BigDecimal price, ordered by minQuantity. Expose service methods that API and cart code can call to load/replace tiers atomically after validation. Enforce all TASK.md validation rules (including no mutation on rejection), and ensure product deletion remains safe. Keep existing product APIs compatible.

Other parts provide/consume:
- Part 2 will call your tier service methods (name them clearly, e.g. get/replace tiers) after resolving Product via ProductService and store ownership.
- Part 3 will call your product/tier accessor or tier service while recalculating cart item prices; ensure access works for each item's Product and special/base price.
