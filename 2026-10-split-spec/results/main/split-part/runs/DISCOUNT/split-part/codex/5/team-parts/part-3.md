Part 3 – shopper promo application and cart totals

Implement shopper-facing promo behavior and cart serialization/calculation. Own cart API/facade/populator/model files and core order-total/promo module files (including removal of hard-coded rules use), but do not edit discount persistence/service or admin API files.

Requirements (exact task wording):
- Shoppers apply a code with the existing POST /api/v1/cart/{cartCode}/promo/{code}. Codes match ignoring case.
- A code applies to a cart only if it belongs to the cart's store, is active, today is between its start and end dates (inclusive), the cart's subtotal is at least its minimum, and the cart has at least one eligible item.
- With categories, only items whose product is in one of those categories, or in any category below them, are eligible. Without categories, every item is.
- PERCENT takes that percentage off the eligible items' subtotal. AMOUNT takes that amount off, but never more than the eligible items' subtotal. The discount is rounded to 2 decimal places, halves rounding up.
- Applying a code that does not apply is rejected with HTTP 400 Bad Request, and the cart keeps the code it had before, if any. Applying a code that applies replaces any previous code: a cart has at most one.
- The cart, whenever it is returned, shows the applied code in "promoCode" (as the merchant wrote it), a line in "totals" with code "discount" and the discount as a positive "value", and a "total" that is the subtotal minus the discount.
- The discount is worked out again every time the cart is returned. If the cart or the code changes so that the code no longer applies (items removed, the code deactivated, edited or deleted), the cart drops it: "promoCode" is empty and there is no discount line.
- An applied code no longer expires after one day; it stays on the cart for as long as it applies.
- Test1234 no longer gives any discount, unless a merchant creates it as a code.

Call Part 1's case-insensitive lookup/eligibility calculation service. Ensure failed application leaves the previous promo unchanged and maps failures to HTTP 400. Recalculate on every cart response and remove stale promo state.

Other parts provide/consume: Part 1 supplies discount lookup and calculation; Part 2 exposes merchant CRUD but needs no cart changes.
