# Part 3: cart pricing and returned totals

Read `TASK.md` first. Update cart calculation/population so every cart response recalculates each line's effective unit price from that line product's own tiers and quantity, using the greatest reached minQuantity but never overriding a lower product/special price. Recompute line `subTotal`, cart `subtotal`, and `total` on every return/change, including existing carts after tier edits; avoid stale stored prices and keep product deletion behavior intact.

Files owned: `sm-core/src/main/java/com/salesmanager/core/business/services/shoppingcart/**` and related order/cart calculation classes, `sm-core-model/src/main/java/com/salesmanager/core/model/shoppingcart/**`, plus cart mappers/populators and cart API DTO code under `sm-shop/src/main/java/com/salesmanager/shop/**` as needed. You may add focused cart tests under `sm-core/src/test` or `sm-shop/src/test`.

Other parts provide/consume: Part 1 supplies tier data on the core Product (or a service lookup) and its effective-price semantics. Part 2 owns only admin HTTP and does not need changes from this part.
