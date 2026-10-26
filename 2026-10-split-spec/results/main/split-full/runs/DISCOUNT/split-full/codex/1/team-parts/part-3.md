## Part 3: shopper promo application and cart totals

Read `TASK.md` first, then implement the cart-side behavior only.

Files owned (create or modify only these, unless a compile fix is absolutely required):
- `sm-shop/src/main/java/com/salesmanager/shop/store/controller/shoppingCart/facade/ShoppingCartFacadeImpl.java`
- `sm-shop/src/main/java/com/salesmanager/shop/mapper/cart/ReadableShoppingCartMapper.java`
- `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/shoppingCart/ShoppingCartApi.java` (only if status/error handling needs it)
- `sm-core/src/main/java/com/salesmanager/core/business/modules/order/total/PromoCodeCalculatorModule.java`
- `sm-core/src/main/resources/com/salesmanager/drools/rules/PromoCoupon.drl` (remove hard-coded Test1234 behavior)
- `sm-core/src/main/java/com/salesmanager/core/business/services/order/OrderServiceImpl.java` and related cart/order calculation files only where required to remove one-day expiry and recalculate dynamic discounts

Use Part 1's discount lookup/evaluation service. Applying `/cart/{cartCode}/promo/{code}` must reject non-applicable codes with 400 while preserving a previous code; valid codes replace the previous one. Every cart read recalculates eligibility and discount, clears stale/deleted/deactivated codes, emits `promoCode`, a positive `discount` total line, and subtotal-minus-discount total. Honor category descendants, minimum subtotal, dates, store ownership, amount cap, percentage/amount rounding, and merchant casing. Do not implement admin CRUD or change Part 1 files.
