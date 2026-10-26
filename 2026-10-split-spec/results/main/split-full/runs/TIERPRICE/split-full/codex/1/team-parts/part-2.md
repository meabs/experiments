Part 2 owns the admin REST API for product quantity tiers.

Add protected v1 endpoints exactly as specified by TASK.md:

- `PUT /api/v1/private/product/{id}/tiers` with a JSON list, replacing all tiers and returning HTTP 200 plus the stored ordered list.
- `GET /api/v1/private/product/{id}/tiers` returning the ordered list.

Use the same `MerchantStore` argument/security conventions as the existing private product APIs, so `?store=` selects the store. Unknown products and products belonging to another store must become 404. Malformed or rule-violating tier payloads must become 400, with no partial write. Preserve JSON names `minQuantity` and `price` and return lowest minQuantity first.

Files owned (and only these unless a compile fix is unavoidable):

- `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/ProductTierApi.java` (new controller; or the closest single v1 product API file if you choose to add methods there)
- `sm-shop-model/src/main/java/com/salesmanager/shop/model/catalog/product/ProductTier.java` (new request/response DTO only if the core entity should not be exposed)

The domain service is Part 1's `ProductTierService` with `getTiers(...)` and `replaceTiers(...)`. Do not implement cart pricing here; Part 3 owns that.
