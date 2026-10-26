Part 1 owns the quantity-tier domain and persistence contract.

Implement the tier entity/model and its persistence/service layer, including validation and atomic replacement semantics required by TASK.md. Tiers must be associated with products, isolated by product/store, ordered by minQuantity, and removed safely when a product is deleted. Expose a service that the API and cart can call; use clear methods equivalent to:

- `List<ProductTier> getTiers(Long productId, MerchantStore store)`
- `List<ProductTier> replaceTiers(Long productId, MerchantStore store, List<ProductTier> tiers)`
- `BigDecimal priceForQuantity(Product product, int quantity)` (or an equivalently named method)

The service must reject invalid tier lists without changing stored data, and must preserve the product's existing tiers on failure. It should provide the product/store lookup behavior needed for 404 handling by the API.

Files owned (and only these unless a compile fix is unavoidable):

- `sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/ProductTier.java` (new)
- `sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/Product.java` (tier relationship/cascade)
- `sm-core/src/main/java/com/salesmanager/core/business/repositories/catalog/product/ProductTierRepository.java` (new, plus any tier repository implementation if needed)
- `sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/ProductTierService.java` (new)
- `sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/ProductTierServiceImpl.java` (new)

Part 2 will call the service methods above and serialize `ProductTier` (or adapt it to its API DTO). Part 3 will call `priceForQuantity` while recalculating cart lines; it will continue to obtain the base/special product price through the existing pricing service and must choose the lower applicable price.
