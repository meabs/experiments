Part 3 — cart tier pricing and totals

Update cart calculation/population so every returned cart reflects current product tiers and line quantities. Reprice each line from that line's own Product tiers on every cart read/recalculation, including carts already stored before a tier update.

Files owned:
- sm-core/src/main/java/com/salesmanager/core/business/services/shoppingcart/**
- sm-core/src/main/java/com/salesmanager/core/business/services/order/** (only cart-total pricing changes)
- sm-shop/src/main/java/com/salesmanager/shop/populator/shoppingCart/**

Requirements (exact task wording):
- “In a cart, a line's unit price is the price of the tier with the largest minQuantity that the line's quantity reaches. If no tier is reached, or the product's own price (including any special price) is lower than the tier's, the product's own price applies.”
- “The cart, whenever it is returned, shows each line's \"subTotal\" (unit price × quantity), and the cart's \"subtotal\" and \"total\", at these prices. They are worked out again every time: changing a line's quantity, or changing the product's tiers, reprices carts that already hold it.”
- “Each line is priced only on its own product's tiers.”
- “A product with tiers can still be deleted as before.”

Ensure quantity changes trigger recalculation and tier changes are observed without requiring cart edits. Preserve special/product pricing precedence, use the largest reached minQuantity, and update line itemPrice/subTotal plus cart subtotal/total before response serialization.

Other parts provide:
- Part 1 provides Product tier access and a resolver (expected ProductTierService.resolvePrice(Product, quantity, ownPrice) or equivalent).
- Part 2 provides only the admin API; no cart/controller coupling is required.
