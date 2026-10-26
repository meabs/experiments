Part 3 — cart tier pricing and totals

Implement cart repricing integration. Own only files under sm-core/src/main/java/com/salesmanager/core/business/services/shoppingcart/**, sm-core/src/main/java/com/salesmanager/core/business/services/order/**, sm-shop/src/main/java/com/salesmanager/shop/mapper/cart/**, sm-shop/src/main/java/com/salesmanager/shop/populator/shoppingCart/**, and closely related cart model files only if needed. Do not edit tier API or tier persistence files.

Requirements (exact task wording):
- “In a cart, a line's unit price is the price of the tier with the largest minQuantity that the line's quantity reaches. If no tier is reached, or the product's own price (including any special price) is lower than the tier's, the product's own price applies.”
- “The cart, whenever it is returned, shows each line's \"subTotal\" (unit price × quantity), and the cart's \"subtotal\" and \"total\", at these prices. They are worked out again every time: changing a line's quantity, or changing the product's tiers, reprices carts that already hold it.”
- “Each line is priced only on its own product's tiers.”
- “A product with tiers can still be deleted as before.”

Use ProductTierService.priceForQuantity (from Part 1) or equivalent and ensure every cart-return/recalculation path refreshes line unit price and subtotal before totals are exposed. Preserve special-price precedence and avoid applying one product's tiers to another line. Run focused cart tests or module tests.
