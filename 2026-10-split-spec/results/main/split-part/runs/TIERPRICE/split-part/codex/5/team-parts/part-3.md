# Part 3 — dynamic cart tier pricing

## Scope

Make cart lines and cart totals use the current product tiers on every cart response and quantity update. Do not edit product persistence or admin API files; consume Part 1's `productTierService`.

## Files owned

- `sm-core/src/main/java/com/salesmanager/core/business/services/shoppingcart/ShoppingCartServiceImpl.java`
- `sm-shop/src/main/java/com/salesmanager/shop/store/controller/shoppingCart/facade/ShoppingCartFacadeImpl.java`
- `sm-shop/src/main/java/com/salesmanager/shop/populator/shoppingCart/ShoppingCartDataPopulator.java`
- `sm-shop/src/main/java/com/salesmanager/shop/populator/shoppingCart/ShoppingCartModelPopulator.java` (only if needed to preserve/recompute pricing)

## Requirements (exact task wording)

Wholesale buyers want a lower unit price when they buy more of a product. Add quantity price tiers: each store's admins set them per product, and the cart prices each line by the tier its quantity reaches.

- In a cart, a line's unit price is the price of the tier with the largest minQuantity that the line's quantity reaches. If no tier is reached, or the product's own price (including any special price) is lower than the tier's, the product's own price applies.
- The cart, whenever it is returned, shows each line's "subTotal" (unit price × quantity), and the cart's "subtotal" and "total", at these prices. They are worked out again every time: changing a line's quantity, or changing the product's tiers, reprices carts that already hold it.
- Each line is priced only on its own product's tiers.
- A product with tiers can still be deleted as before.

## Integration contract

Inject/use Part 1's `productTierService.resolveUnitPrice(Product product, int quantity, BigDecimal ownPrice)` for every line. Preserve existing special-price calculation first, then compare the tier price against that own final price. Recompute `itemPrice`, `subTotal`, and aggregate subtotal/total whenever a cart is loaded or returned, not only when an item is first added. Ensure quantity update paths also invoke the same recalculation and that lines never borrow tiers from another product. Keep the existing display formatting and promotion/tax behavior except for the unit-price substitution.

## Checks

Run focused cart/core/shop tests or Maven test commands that exercise cart add, quantity update, and cart retrieval. Report any failures.
