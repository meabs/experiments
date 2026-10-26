# Part 2 — shopper promo endpoint and cart representation

## Scope and owned files

Own shopper-facing promo application and cart output: `sm-shop` cart API/controller, `ShoppingCartFacade`/`ShoppingCartFacadeImpl` promo flow, and `ReadableShoppingCartMapper`/shop cart DTO mapping. Modify only those cart API/facade/mapper files (and directly associated shop cart model files if required). Do not edit discount persistence/admin files (part 1) or pricing/order-total modules (part 3).

## Requirements (exact task wording)

Rules:

- Shoppers apply a code with the existing POST /api/v1/cart/{cartCode}/promo/{code}. Codes match ignoring case.
- Applying a code that does not apply is rejected with HTTP 400 Bad Request, and the cart keeps the code it had before, if any. Applying a code that applies replaces any previous code: a cart has at most one.
- The cart, whenever it is returned, shows the applied code in "promoCode" (as the merchant wrote it), a line in "totals" with code "discount" and the discount as a positive "value", and a "total" that is the subtotal minus the discount.
- The discount is worked out again every time the cart is returned. If the cart or the code changes so that the code no longer applies (items removed, the code deactivated, edited or deleted), the cart drops it: "promoCode" is empty and there is no discount line.
- An applied code no longer expires after one day; it stays on the cart for as long as it applies.

## Contracts from other parts

Part 1 provides a `DiscountService` lookup by merchant store and case-insensitive code, returning the stored discount (including its canonical merchant-written `code`). Part 3 provides the calculation/revalidation hook or service used when a cart is read. Call that hook on every cart return and clear the persisted promo when it is no longer applicable. Preserve the old promo when an attempted replacement is rejected; only persist a new promo after validation succeeds.

The existing endpoint remains `/api/v1/cart/{cartCode}/promo/{code}` and must translate an invalid/non-applicable code to HTTP 400.
