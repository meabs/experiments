Part 3 — cart tier pricing and returned totals

Update cart/order pricing so every recalculation derives each line’s unit price from that line’s own product tiers and quantity, compares against the product’s normal/special final price, and updates line subtotal and cart totals. Ensure this happens whenever a cart is returned, after quantity changes, and after tier changes for products already in carts. Update both current cart mapping paths if needed so JSON exposes subTotal, subtotal, and total at recalculated prices.

Files owned (and only these unless a directly required adjacent test is needed):
- sm-core/src/main/java/com/salesmanager/core/business/services/order/**
- sm-core/src/main/java/com/salesmanager/core/business/services/shoppingcart/**
- sm-core/src/main/java/com/salesmanager/core/model/shoppingcart/**
- sm-shop/src/main/java/com/salesmanager/shop/mapper/cart/**
- sm-shop/src/main/java/com/salesmanager/shop/populator/shoppingCart/**
- sm-shop/src/main/java/com/salesmanager/shop/store/controller/shoppingCart/facade/**

Exact task requirements applying to this part:
- “In a cart, a line's unit price is the price of the tier with the largest minQuantity that the line's quantity reaches. If no tier is reached, or the product's own price (including any special price) is lower than the tier's, the product's own price applies.”
- “The cart, whenever it is returned, shows each line's \"subTotal\" (unit price × quantity), and the cart's \"subtotal\" and \"total\", at these prices. They are worked out again every time: changing a line's quantity, or changing the product's tiers, reprices carts that already hold it.”
- “Each line is priced only on its own product's tiers.”
- “A product with tiers can still be deleted as before.”

Other parts provide/rely on:
- Part 1 provides persisted per-product tiers and a deterministic lookup/service; use the product’s own tiers only.
- Part 2 provides the admin endpoint that can replace tiers; cart responses must observe those changes on the next calculation without requiring cart edits.
