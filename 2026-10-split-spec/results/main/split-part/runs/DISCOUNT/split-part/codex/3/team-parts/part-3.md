# Part 3 — shopper promo endpoint, cart state, and totals

## Scope and owned files

Own all new or modified cart/promo files under `sm-shop/src/main/java/com/salesmanager/shop/store/controller/shoppingCart/`, `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/shoppingCart/`, `sm-shop/src/main/java/com/salesmanager/shop/mapper/cart/`, and relevant `sm-shop-model` cart DTO files; also own existing promo/total/order calculation files under `sm-core/src/main/java/com/salesmanager/core/business/modules/order/total/` and `sm-core/src/main/java/com/salesmanager/core/business/services/order/` if required. Do not edit discount entity/repository/service or admin API files owned by Parts 1–2.

Replace the hard-coded Drools/Test1234 behavior. Make `POST /api/v1/cart/{cartCode}/promo/{code}` validate/apply through Part 1's service, preserve the old code when a new code is invalid, and replace it when valid. Remove the one-day promo expiry. On every cart read/recalculation, re-evaluate the stored code; clear it when deleted/deactivated/edited or otherwise inapplicable. Ensure readable cart JSON exposes promoCode, a positive `discount` total line, and subtotal-minus-discount total, with proper half-up 2-decimal rounding and category descendants.

## Exact task requirements applying to this part

Shoppers apply a code with the existing POST /api/v1/cart/{cartCode}/promo/{code}. Codes match ignoring case.

- A code applies to a cart only if it belongs to the cart's store, is active, today is between its start and end dates (inclusive), the cart's subtotal is at least its minimum, and the cart has at least one eligible item.
- With categories, only items whose product is in one of those categories, or in any category below them, are eligible. Without categories, every item is.
- PERCENT takes that percentage off the eligible items' subtotal. AMOUNT takes that amount off, but never more than the eligible items' subtotal. The discount is rounded to 2 decimal places, halves rounding up.
- Applying a code that does not apply is rejected with HTTP 400 Bad Request, and the cart keeps the code it had before, if any. Applying a code that applies replaces any previous code: a cart has at most one.
- The cart, whenever it is returned, shows the applied code in "promoCode" (as the merchant wrote it), a line in "totals" with code "discount" and the discount as a positive "value", and a "total" that is the subtotal minus the discount.
- The discount is worked out again every time the cart is returned. If the cart or the code changes so that the code no longer applies (items removed, the code deactivated, edited or deleted), the cart drops it: "promoCode" is empty and there is no discount line.
- An applied code no longer expires after one day; it stays on the cart for as long as it applies.
- Test1234 no longer gives any discount, unless a merchant creates it as a code.

## What other parts provide / rely on

Part 1 provides `DiscountService` case-insensitive lookup/evaluation and a result with applicability, eligible subtotal, and rounded discount. Part 2 provides persisted merchant codes through that service. Preserve existing cart facade method names and response DTO shape while adding the required totals fields.
