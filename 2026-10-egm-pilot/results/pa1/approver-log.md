## Given to the approver

You are a senior engineer on the shopizer team (a Java e-commerce platform). You asked for the feature below, and an AI coding agent is now designing it. Before any code is written, you review its work. Once you approve the design, a different coding agent, which sees only the approved design file, will build it.

The agent works in this checkout: ~/code/benchmark/skills-impact-work/egm-runs/pa1/repo
You may read files there (the design it writes is `design_draft.md` at its root, and other reports may appear beside it) to check what the design says about the code. Do not read or search anything outside that folder, and do not create, edit or delete any file. Do not run builds or tests.

I will pass you each message the agent sends, verbatim. Reply with only the message you want sent back to it, nothing else: it is sent verbatim. Use your judgement as the engineer who asked for this: approve, push back, ask for changes or more detail, answer its questions, or choose among the options it offers. You want the feature built correctly and completely, as the request describes; you do not want scope added that the request does not ask for. When the agent offers numbered or lettered options, say which you choose and why, briefly. You have at most 25 messages in all, so be decisive.

When you consider the design ready to hand to the builder and there is nothing left to approve, reply with exactly: APPROVED FOR BUILD

The feature request, as you wrote it:

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

---

The agent's message:

Design is ready in [design_draft.md](~/code/benchmark/skills-impact-work/egm-runs/pa1/repo/design_draft.md).

No application code was changed.

- tool call `Read`: `{"file_path": "~/code/benchmark/skills-impact-work/egm-runs/pa1/repo/design_draft.md"}`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/pa1/repo; ls; grep -rn \"lineage\" --include=Category.java . | head; grep -rn \"promo\" --include=*.java sm-shop/src/main/java | grep -v \"^.*://\" | head -40; grep -rn \"DeleteMapping\\|ResponseStatus(HttpStatus\" sm-shop/src/m`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/pa1/repo; sed -n 215,240p sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/category/CategoryApi.java; grep -rn \"promo\" sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/shoppingCart/*.java | head; grep -rln \"pr`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/pa1/repo; sed -n 115,150p sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/shoppingCart/ShoppingCartApi.java; grep -n \"promo\\|Promo\" sm-shop/src/main/java/com/salesmanager/shop/mapper/cart/ReadableShoppingCartMapper.j`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/pa1/repo; grep -n \"lineage\\|Lineage\" sm-core/src/main/java/com/salesmanager/core/business/services/catalog/category/CategoryServiceImpl.java | head -8; grep -rn \"authorizedStore\" sm-shop/src/main/java | head -3; grep -rln \`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/pa1/repo; grep -n \"ExceptionHandler\\|ResponseStatus\\|class\" sm-shop/src/main/java/com/salesmanager/shop/store/api/exception/RestErrorHandler.java; sed -n 25,50p sm-shop/src/main/java/com/salesmanager/shop/utils/Authorization`

## Approver's reply

The design is mostly sound, but some points are left open and the builder will only see this file. Please settle each one below in design_draft.md, then send it back.

1. Errors from malformed JSON. RestErrorHandler has an `@ExceptionHandler(Exception.class)` that returns 500, and it will catch Jackson's `HttpMessageNotReadableException` / `InvalidFormatException`. As written, an unknown "type" (e.g. "FIXED"), a malformed date or a non-numeric value would come back as 500. State the mechanism. Either have the DTO take `type`, `startDate` and `endDate` as Strings and parse/validate them in the service, or add an explicit handler that maps those exceptions to 400. I prefer the String fields, because then all validation sits in one place. Add a new `ConflictException` (or similar) with a 409 handler in RestErrorHandler. For 404, reuse the existing `ResourceNotFoundException`. For 400, reuse an existing 400-mapped exception (`ServiceRuntimeException`/`RestApiException`) or add a dedicated one. Name the classes.

2. Shopper promo endpoint. `ShoppingCartApi.modifyCart` catches every Exception and rethrows all but ResourceNotFoundException as ServiceRuntimeException, which happens to map to 400. Say explicitly that an inapplicable code throws the 400 exception and it reaches the client as 400. Say that an unknown cart stays 404. Keep the existing success status (201) and the existing response body.

3. Authorization. "Existing private endpoint conventions" is too vague. Specify `authorizationUtils.authenticatedUser()` plus `authorizeUser(user, [SUPERADMIN, ADMIN, ADMIN_RETAIL], merchantStore)`, the same pattern other private APIs use.

4. DELETE status. Decide it now: return 200 with no body, matching CategoryApi's delete. Don't leave "204 preferred".

5. Category descendants. Make it concrete. Category.lineage is stored as "/1/5/12/" and includes the category's own id. An item is eligible if any of its product's categories has a lineage containing "/<configuredCategoryId>/". Category codes are resolved within the store, case-sensitively as category codes are elsewhere, or say otherwise if the code shows a different convention.

6. Subtotal definition. The "subtotal" used for the minimum check and the eligible subtotal must use the same per-line amount (final unit price × quantity) that the order-total pipeline uses for the cart's "subtotal" total line. That way `total = subtotal - discount` holds exactly against the subtotal in the response. Say which existing method or field supplies it.

7. "Today". Decide it: `LocalDate.now(clock)`, with an injectable `java.time.Clock` bean in the system default zone, used for both the startDate default and eligibility.

8. Empty promoCode. Decide it: `promoCode` is null when no code applies, as the existing mapper already does at line 266. No discount total line.

9. Order path. Keep it minimal. Remove the 1-day `promoAdded` expiry block in OrderServiceImpl (~line 436). Because the new discount is computed inside the shared order-total pipeline, checkout gets the same amount automatically. Don't add other order-side changes beyond what removing Drools and the expiry requires. Drop the "should be used by order checkout/summary paths" wording, or rewrite it as exactly that.

10. Which cart paths recalculate. List the concrete ShoppingCartFacade/mapper methods that return a cart and so must recalculate and clear a stale code: GET /cart/{code}, add/modify item, multi, promo, and the customer cart endpoints if they share the mapper. Then the builder won't miss one.

A few minor confirmations:
- Rejecting a negative minimumSubtotal with 400 is fine.
- De-duplicating categories is fine.
- When the database unique constraint fires, translate the DataIntegrityViolation to 409.
- Leave `promoAdded` in the entity, unused for validity.

## Given to the approver

The coordinator sent a message while you were working:
The agent's message:

Updated [design_draft.md](~/code/benchmark/skills-impact-work/egm-runs/pa1/repo/design_draft.md) with all requested decisions and concrete implementation details. No application code was changed.

Address this before completing your current task.

- tool call `Bash`: `{"command": "cat ~/code/benchmark/skills-impact-work/egm-runs/pa1/repo/design_draft.md"}`

## Approver's reply

APPROVED FOR BUILD
