Part 1 owns the wishlist domain and persistence/service layer. Read TASK.md first.

Implement the entities/DTOs, repository, and service needed to store per-customer/per-store wishlist entries with insertion timestamps, enforce 50-item limit and idempotent adds, resolve product SKU/details and availability, produce ordered customer wishlist data and the top-10 aggregate report, and remove entries when a product is deleted. Integrate with existing Customer, MerchantStore, Product and exception conventions.

Files owned (create or modify only these unless compilation requires a directly related interface):
- sm-core-model/src/main/java/com/salesmanager/core/model/** wishlist model files
- sm-core/src/main/java/com/salesmanager/core/business/repositories/** wishlist repository files
- sm-core/src/main/java/com/salesmanager/core/business/services/** wishlist service files
- sm-shop-model/src/main/java/com/salesmanager/shop/model/** wishlist API DTO files
- sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/ProductServiceImpl.java (only the product-delete cleanup hook)

Provide a public service with methods the API can call, including add(customer, store, sku), get(customer, store), remove(customer, store, sku), move/remove validation support, and popular(store). Keep method names/signatures discoverable and document them in the interface. Other parts rely on this service and DTOs; do not implement controllers or cart facade changes.
