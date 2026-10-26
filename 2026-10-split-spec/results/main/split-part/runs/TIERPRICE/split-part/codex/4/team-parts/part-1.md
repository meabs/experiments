Part 1 — quantity-tier persistence and product pricing support

Implement the domain and service layer for per-product quantity price tiers. Add the tier entity/value type, persistence mapping/repository as needed, and service methods used by the API and cart. Keep tiers owned by Product and ensure deleting a Product still removes/cleans up tiers through the existing delete behavior.

Files owned:
- sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/** (Product and new tier model files)
- sm-core/src/main/java/com/salesmanager/core/business/repositories/catalog/product/** (only tier persistence additions)
- sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/** (only tier-related additions/changes)

Requirements (exact task wording):
- “Wholesale buyers want a lower unit price when they buy more of a product. Add quantity price tiers: each store's admins set them per product, and the cart prices each line by the tier its quantity reaches.”
- “A tier is JSON: {"minQuantity": 10, "price": 90.00}. Tiers are always returned as a list ordered by minQuantity, lowest first.”
- “Rules:”
- “minQuantity is a whole number of at least 2; price is more than 0. A missing minQuantity or price, a minQuantity that is not a whole number, two tiers with the same minQuantity, or more than 10 tiers gives HTTP 400 Bad Request.”
- “A tier for more units must have a lower price than every tier for fewer units; otherwise HTTP 400 Bad Request.”
- “A rejected request changes nothing: the product keeps the tiers it had.”
- “Each line is priced only on its own product's tiers.”
- “A product with tiers can still be deleted as before.”

Provide stable methods/classes for Part 2 and Part 3 to call (for example Product.getQuantityPriceTiers()/setQuantityPriceTiers and a ProductTierService with get/replace/resolvePrice methods). Enforce validation atomically before replacing existing tiers; return tiers sorted by minQuantity.

Other parts provide:
- Part 2 supplies the protected /api/v1/private/product/{id}/tiers controller and JSON DTO binding, invoking your tier service and product/store lookup.
- Part 3 supplies cart integration and calls your tier price resolver against each line's Product and quantity.
