Part 1 — tier persistence and product domain

Implement the quantity-tier domain and persistence layer. Own only these files (new files are allowed under these directories):

- `sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/Product.java`
- `sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/tier/` (all new tier entity/model files)
- `sm-core/src/main/java/com/salesmanager/core/business/repositories/catalog/product/tier/` (new repository files)
- `sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/tier/` (new service files)
- `sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/ProductService.java` and `ProductServiceImpl.java` only if needed to expose tier operations

Requirements from TASK.md that apply to this part (exact wording):

"Wholesale buyers want a lower unit price when they buy more of a product. Add quantity price tiers: each store's admins set them per product, and the cart prices each line by the tier its quantity reaches."

"A tier is JSON: {\"minQuantity\": 10, \"price\": 90.00}. Tiers are always returned as a list ordered by minQuantity, lowest first."

"Rules:

- minQuantity is a whole number of at least 2; price is more than 0. A missing minQuantity or price, a minQuantity that is not a whole number, two tiers with the same minQuantity, or more than 10 tiers gives HTTP 400 Bad Request.
- A tier for more units must have a lower price than every tier for fewer units; otherwise HTTP 400 Bad Request.
- A rejected request changes nothing: the product keeps the tiers it had."

"A product with tiers can still be deleted as before."

Provide a stable service API for the API part, preferably methods named `getTiers(Product)`, `replaceTiers(Product,List<...>)`, and/or `getTiers(Long,MerchantStore)` that atomically validates then replaces and returns tiers sorted ascending. The API coder will call this service and rely on Product's tier accessor; the cart coder will read the same Product tier collection/service. Keep store ownership checks possible through `ProductService.retrieveById`/`findOne`.

Run focused module tests or compilation if practical.
