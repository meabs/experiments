# Part 3 — cart tier pricing and totals

Read `TASK.md` first. Make cart calculations apply the best reached tier for each line, dynamically on every cart read/recalculation, while preserving the product's own (including special) price whenever it is lower than a tier.

Own these files:

- `sm-core/src/main/java/com/salesmanager/core/business/services/order/**` and related shopping-cart calculation code where line prices and order totals are computed.
- `sm-shop/src/main/java/com/salesmanager/shop/populator/shoppingCart/**` and shopping-cart response mapping needed to expose each line `subTotal` plus cart `subtotal`/`total`.

Ensure changing quantity or changing stored tiers reprices an existing cart, each line consults only its own Product's tiers, and line subtotal is unit price × quantity. Use Part 1's tier service/accessors; do not implement REST endpoints or alter tier persistence. Keep existing tax/discount behavior coherent and run focused cart/order tests.
