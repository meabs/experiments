# Part 3 — discount eligibility and totals calculation

## Scope and owned files

Own discount computation and order/cart total integration: `sm-core` pricing/order-total modules, shopping-cart calculation service integration, legacy promo rule removal, and any core model fields needed strictly by that calculation. Do not edit the admin API/domain files (part 1) or shopper controller/facade/mapper files (part 2).

## Requirements (exact task wording)

Rules:

- A code applies to a cart only if it belongs to the cart's store, is active, today is between its start and end dates (inclusive), the cart's subtotal is at least its minimum, and the cart has at least one eligible item.
- With categories, only items whose product is in one of those categories, or in any category below them, are eligible. Without categories, every item is.
- PERCENT takes that percentage off the eligible items' subtotal. AMOUNT takes that amount off, but never more than the eligible items' subtotal. The discount is rounded to 2 decimal places, halves rounding up.
- The discount is worked out again every time the cart is returned. If the cart or the code changes so that the code no longer applies (items removed, the code deactivated, edited or deleted), the cart drops it: "promoCode" is empty and there is no discount line.
- An applied code no longer expires after one day; it stays on the cart for as long as it applies.
- Test1234 no longer gives any discount, unless a merchant creates it as a code.

## Contracts from other parts

Part 1 provides the discount entity/service lookup and category data. Part 2 invokes your eligibility/recalculation hook while rendering a cart and expects a result containing applicability, canonical promo code, and positive discount amount (or an empty/zero result when invalid). Integrate with existing subtotal/totals conventions so the returned total equals subtotal minus discount and the discount line uses code `discount`.

Remove/bypass the hard-coded `Test1234` Drools behavior; no code receives special treatment unless present in the merchant discount store. Keep calculations store-aware and category-descendant aware.
