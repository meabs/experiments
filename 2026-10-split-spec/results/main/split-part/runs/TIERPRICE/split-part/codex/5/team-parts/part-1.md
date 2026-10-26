# Part 1 — quantity-tier model and core service

## Scope

Implement persistent per-product quantity price tiers and the core service used by the API and cart. Do not edit files outside the ownership list unless a compile fix is unavoidable; coordinate any such need with the planner.

## Files owned

- `sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/Product.java`
- `sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/ProductTier.java` (new)
- `sm-core/src/main/java/com/salesmanager/core/business/repositories/catalog/product/ProductTierRepository.java` (new)
- `sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/ProductTierService.java` (new)
- `sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/ProductTierServiceImpl.java` (new)

## Requirements (exact task wording)

Wholesale buyers want a lower unit price when they buy more of a product. Add quantity price tiers: each store's admins set them per product, and the cart prices each line by the tier its quantity reaches.

- A tier is JSON: {"minQuantity": 10, "price": 90.00}. Tiers are always returned as a list ordered by minQuantity, lowest first.
- minQuantity is a whole number of at least 2; price is more than 0. A missing minQuantity or price, a minQuantity that is not a whole number, two tiers with the same minQuantity, or more than 10 tiers gives HTTP 400 Bad Request.
- A tier for more units must have a lower price than every tier for fewer units; otherwise HTTP 400 Bad Request.
- A rejected request changes nothing: the product keeps the tiers it had.
- In a cart, a line's unit price is the price of the tier with the largest minQuantity that the line's quantity reaches. If no tier is reached, or the product's own price (including any special price) is lower than the tier's, the product's own price applies.
- Each line is priced only on its own product's tiers.
- A product with tiers can still be deleted as before.

## Contract for other parts

Expose a Spring service named `productTierService` with methods equivalent to:

- `List<ProductTier> getTiers(Product product)` (ordered by `minQuantity` ascending)
- `List<ProductTier> getTiers(Long productId, MerchantStore store)` (return empty or throw a not-found signal when the product is absent/wrong store; API must map that to 404)
- `List<ProductTier> replaceTiers(Product product, List<ProductTier> tiers)` (validate and atomically replace; invalid input must leave existing rows untouched)
- `BigDecimal resolveUnitPrice(Product product, int quantity, BigDecimal ownPrice)` (apply largest reached tier only when it is cheaper than own price)

The entity should map each tier to exactly one product, cascade removal when a product is deleted, and preserve the product's existing deletion behavior. Use normal JPA table/id conventions in this repository. Ensure returned tier lists are deterministic and sorted.

## Checks

Run focused Maven compilation/tests for `sm-core-model` and `sm-core` (or the narrowest useful command) and report failures.
