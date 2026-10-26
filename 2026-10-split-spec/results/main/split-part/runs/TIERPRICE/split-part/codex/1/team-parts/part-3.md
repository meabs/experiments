Part 3 — cart tier pricing and recalculation

Implement cart pricing integration. Own only these files (new files are allowed under these directories):

- `sm-shop/src/main/java/com/salesmanager/shop/store/controller/shoppingCart/facade/ShoppingCartFacadeImpl.java`
- `sm-shop/src/main/java/com/salesmanager/shop/populator/shoppingCart/ShoppingCartDataPopulator.java`
- `sm-shop/src/main/java/com/salesmanager/shop/mapper/cart/ReadableShoppingCartMapper.java`
- `sm-shop/src/main/java/com/salesmanager/shop/populator/shoppingCart/ShoppingCartModelPopulator.java`
- `sm-core/src/main/java/com/salesmanager/core/business/services/shoppingcart/ShoppingCartCalculationService*.java` only if required for recalculation
- `sm-core-model/src/main/java/com/salesmanager/core/model/shoppingcart/ShoppingCartItem.java` and `ShoppingCart.java` only if required for derived prices

Requirements from TASK.md that apply to this part (exact wording):

"In a cart, a line's unit price is the price of the tier with the largest minQuantity that the line's quantity reaches. If no tier is reached, or the product's own price (including any special price) is lower than the tier's, the product's own price applies."

"The cart, whenever it is returned, shows each line's \"subTotal\" (unit price × quantity), and the cart's \"subtotal\" and \"total\", at these prices. They are worked out again every time: changing a line's quantity, or changing the product's tiers, reprices carts that already hold it."

"Each line is priced only on its own product's tiers."

"A product with tiers can still be deleted as before."

Recompute from current Product data whenever a cart response is built (including existing carts after tier changes), and when quantities change. Preserve special-price logic and existing cart response field names. Depend on Part 1’s Product tier accessor/entity (expected `getTiers()` and tier `getMinQuantity()/getPrice()`), and do not edit API/domain files owned by other parts.

Run focused cart/module tests or compilation if practical.
