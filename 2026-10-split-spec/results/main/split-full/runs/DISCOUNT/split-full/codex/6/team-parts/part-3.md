## Part 3 — shopper cart promo behavior

Read `TASK.md` first. Own all cart-side behavior and presentation; do not edit part 1’s discount model/service or part 2’s admin API except for unavoidable compile fixes.

### Files owned

- `sm-shop/src/main/java/com/salesmanager/shop/store/controller/shoppingCart/**` (facade/cart orchestration)
- `sm-shop/src/main/java/com/salesmanager/shop/mapper/cart/**` and shopping-cart populators involved in returned totals
- `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/shoppingCart/ShoppingCartApi.java` only if needed to map invalid promo application to 400
- `sm-core/src/main/java/com/salesmanager/core/business/modules/order/total/PromoCodeCalculatorModule.java` and directly related cart total code if needed
- Cart-focused tests under `sm-shop/src/test/**` or `sm-core/src/test/**` that you add.

### What to implement

Replace the hard-coded/expired Test1234 rule path. `POST /api/v1/cart/{cartCode}/promo/{code}` must case-insensitively find a code for the cart’s store, reject non-applicable codes with 400 while preserving the previous code, and replace an applicable prior code. Recalculate on every cart return: active/date/minimum/category hierarchy/eligible-item checks; percentage or capped amount discount; 2-decimal HALF_UP rounding; promoCode as merchant-entered text; positive `discount` total line; total=subtotal-discount. Drop the code and discount line whenever edits, removals, deactivation, item changes, or dates make it invalid. Remove the one-day promo expiry behavior. Ensure Test1234 has no special treatment.

Use part 1’s service lookup/eligibility/calculation methods and existing cart/product/category data. Preserve store ownership and existing response shapes. Run focused cart/API tests and compile.

### Dependencies supplied by other parts

Part 1 supplies the discount service/domain and calculation contract. Part 2 only exposes CRUD and should not be required for cart internals. Keep cart persistence compatible with the existing `promoCode`/`promoAdded` fields unless the service requires a safe additive change.
