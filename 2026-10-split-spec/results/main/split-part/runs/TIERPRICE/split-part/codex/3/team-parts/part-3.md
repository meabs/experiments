Part 3 — cart tier pricing and returned totals

Scope: update cart pricing/recalculation and cart response mapping so quantity tiers are applied dynamically. Own only sm-core/src/main/java/com/salesmanager/core/business/services/shoppingcart (especially ShoppingCartServiceImpl and calculation code), sm-shop/src/main/java/com/salesmanager/shop/mapper/cart and cart-facing model/populator files needed for returned fields, plus focused cart tests. Do not edit tier persistence or REST API files.

Requirements from TASK.md that apply (exact wording):

- In a cart, a line's unit price is the price of the tier with the largest minQuantity that the line's quantity reaches. If no tier is reached, or the product's own price (including any special price) is lower than the tier's, the product's own price applies.
- The cart, whenever it is returned, shows each line's "subTotal" (unit price × quantity), and the cart's "subtotal" and "total", at these prices. They are worked out again every time: changing a line's quantity, or changing the product's tiers, reprices carts that already hold it.
- Each line is priced only on its own product's tiers.
- A product with tiers can still be deleted as before.

Recalculate from current product/tier data whenever a cart is loaded or returned, including quantity changes; ensure itemPrice, line subTotal, cart subtotal and total all reflect the chosen tier and existing special-price rules. Do not cache stale tier values in persisted cart rows. Preserve variant/attribute behavior and existing cart APIs.

Other parts provide: Part 1 provides an ordered tier read service and tier records; Part 2 exposes administration only. Use the product attached to each ShoppingCartItem so tiers cannot leak across lines/products.
