Part 1 — tier domain model and persistence/service

Do the following. Add the product quantity-tier domain model and the service/repository support needed by the admin API and cart code. Keep tiers owned by the product/store and ensure deleting a product still works. Implement validation/ordering/atomic replacement in a reusable service method so the API can return a rejected request without changing existing tiers.

Files owned (and only these unless a directly required adjacent test is needed):
- sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/** (product model and new tier entity/value types)
- sm-core/src/main/java/com/salesmanager/core/business/repositories/catalog/product/** (tier repository additions/new repository)
- sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/** (tier service additions/new service)

Exact task requirements applying to this part:
- “Add quantity price tiers: each store's admins set them per product, and the cart prices each line by the tier its quantity reaches.”
- “A tier is JSON: {\"minQuantity\": 10, \"price\": 90.00}. Tiers are always returned as a list ordered by minQuantity, lowest first.”
- “Rules:”
- “minQuantity is a whole number of at least 2; price is more than 0. A missing minQuantity or price, a minQuantity that is not a whole number, two tiers with the same minQuantity, or more than 10 tiers gives HTTP 400 Bad Request.”
- “A tier for more units must have a lower price than every tier for fewer units; otherwise HTTP 400 Bad Request.”
- “A rejected request changes nothing: the product keeps the tiers it had.”
- “A product with tiers can still be deleted as before.”

Other parts provide/rely on:
- Part 2 will call the tier service methods you expose (use clear names such as getTiers(product, store) and replaceTiers(product, store, requestedTiers)) and map the tier type to JSON.
- Part 3 will use the product’s tier collection or a tier lookup/service method to choose a unit price during cart recalculation; expose a deterministic ordered lookup and do not make it store-global.
