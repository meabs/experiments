Merchants want to run their own discount codes. Today the only code the shop understands is hard-coded in a rules file (Test1234), and it expired long ago. Replace it with discount codes that each store's admins manage themselves, and that shoppers apply to their cart.

Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):

- POST /api/v1/private/discounts creates a code and returns HTTP 201 with the stored code, including its "id".
- GET /api/v1/private/discounts lists the store's codes.
- PUT /api/v1/private/discounts/{id} replaces a code; DELETE /api/v1/private/discounts/{id} removes it.
- A code is JSON: {"code": "SPRING10", "type": "PERCENT" or "AMOUNT", "value": 10, "minimumSubtotal": 100.00, "startDate": "2026-01-01", "endDate": "2026-12-31", "categories": ["shoes"], "active": true}. "minimumSubtotal", "endDate" and "categories" are optional (category codes); "active" defaults to true; "startDate" defaults to today.

Rules:

- Codes are unique within a store, ignoring case; creating or renaming to a code that already exists gives HTTP 409 Conflict. Different stores may use the same code.
- A PERCENT value must be more than 0 and at most 100; an AMOUNT value must be more than 0 (an amount in the store's currency). An end date before the start date, an unknown type or category, or a missing code or value gives HTTP 400 Bad Request.
- Shoppers apply a code with the existing POST /api/v1/cart/{cartCode}/promo/{code}. Codes match ignoring case.
- A code applies to a cart only if it belongs to the cart's store, is active, today is between its start and end dates (inclusive), the cart's subtotal is at least its minimum, and the cart has at least one eligible item.
- With categories, only items whose product is in one of those categories, or in any category below them, are eligible. Without categories, every item is.
- PERCENT takes that percentage off the eligible items' subtotal. AMOUNT takes that amount off, but never more than the eligible items' subtotal. The discount is rounded to 2 decimal places, halves rounding up.
- Applying a code that does not apply is rejected with HTTP 400 Bad Request, and the cart keeps the code it had before, if any. Applying a code that applies replaces any previous code: a cart has at most one.
- The cart, whenever it is returned, shows the applied code in "promoCode" (as the merchant wrote it), a line in "totals" with code "discount" and the discount as a positive "value", and a "total" that is the subtotal minus the discount.
- The discount is worked out again every time the cart is returned. If the cart or the code changes so that the code no longer applies (items removed, the code deactivated, edited or deleted), the cart drops it: "promoCode" is empty and there is no discount line.
- An applied code no longer expires after one day; it stays on the cart for as long as it applies.
- Test1234 no longer gives any discount, unless a merchant creates it as a code.
