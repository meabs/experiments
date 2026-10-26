Part 3 owns cart repricing and cart response totals.

Integrate quantity-tier pricing into the existing cart calculation path. Every cart retrieval/return and quantity change must recalculate each line using only that line's product tiers. Pick the largest reached minQuantity, then use the product's own effective base/special price whenever it is lower or no tier is reached. Update line `itemPrice`/`subTotal`, cart subtotal, and total consistently, including carts already persisted before a tier change.

Files owned (and only these unless a compile fix is unavoidable):

- `sm-core/src/main/java/com/salesmanager/core/business/services/shoppingcart/ShoppingCartServiceImpl.java`
- `sm-core/src/main/java/com/salesmanager/core/business/services/order/OrderServiceImpl.java` (only if needed for subtotal/total calculation)
- `sm-shop/src/main/java/com/salesmanager/shop/mapper/cart/ReadableShoppingCartMapper.java`
- any directly corresponding cart calculation test files under `sm-core/src/test` or `sm-shop/src/test` if you add tests

Use Part 1's `ProductTierService.priceForQuantity(Product, int)` (or its equivalent) and the existing `PricingService`/`FinalPrice` logic. Do not alter the admin endpoints or tier validation; Part 2 owns the API and Part 1 owns persistence/validation.
