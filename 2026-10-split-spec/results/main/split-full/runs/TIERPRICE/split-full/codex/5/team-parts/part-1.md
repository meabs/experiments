# Part 1: tier domain and persistence

Read `TASK.md` first. Own the core/domain persistence side of quantity price tiers. Add the tier entity/value type and its product association, repositories/services, and any product-service integration needed to atomically replace/read tiers for a product scoped to a `MerchantStore`. Enforce all request-independent invariants that belong in the service (quantity/price shape, duplicate quantities, maximum 10, strictly decreasing prices as quantities rise) and preserve existing tiers on rejected replacement. Ensure product deletion remains safe with tiers.

Files owned: `sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/**` (tier entity and Product association), `sm-core/src/main/java/com/salesmanager/core/business/repositories/catalog/product/**`, and `sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/**` (including new tier service classes). You may add focused tests under corresponding core modules.

Other parts provide/consume: Part 2 will call your public tier service methods (use clear methods such as `getTiers(productId, store)` and `replaceTiers(productId, store, tiers)`); Part 3 will use a product/tier lookup or `getTiers` to price cart lines. Keep APIs usable without coupling to web DTOs.
