# Part 3 — cart tier pricing and totals

Read `TASK.md` first. Update cart calculation and API response mapping so every cart read recalculates each line’s effective unit price from that line product’s tiers and quantity, choosing the largest reached minQuantity but never charging more than the product’s own effective (including special) price. Recompute line `subTotal`, cart `subtotal`, and `total` on every return, including after quantity/tier changes; keep pricing isolated per product.

Files owned: `sm-core/src/main/java/com/salesmanager/core/business/services/shoppingcart/**` and related order/cart pricing classes only when required, plus `sm-shop/src/main/java/com/salesmanager/shop/populator/shoppingCart/**`, `sm-shop/src/main/java/com/salesmanager/shop/mapper/cart/**`, and corresponding cart model DTO files under `sm-shop/src/main/java/com/salesmanager/shop/model/shoppingcart/**` if needed. Do not edit product tier domain or admin API files.

Other parts provide: Part 1 supplies product tier access (tier objects and getters/service methods). Part 2 exposes administration only. Preserve existing cart/customer/store APIs and currency/display formatting.
