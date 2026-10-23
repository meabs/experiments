## Given to the approver

You are a senior engineer on the shopizer team (a Java e-commerce platform). You asked for the feature below, and an AI coding agent is now designing it. Before any code is written, you review its work. Once you approve the design, a different coding agent, which sees only the approved design file, will build it.

The agent works in this checkout: ~/code/benchmark/skills-impact-work/egm-runs/pa3/repo
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

Design is ready in [design_draft.md](~/code/benchmark/skills-impact-work/egm-runs/pa3/repo/design_draft.md).

No production code was changed.

- tool call `Read`: `{"file_path": "~/code/benchmark/skills-impact-work/egm-runs/pa3/repo/design_draft.md"}`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/pa3/repo; ls; grep -rn \"promo\" --include=*.java sm-shop/src/main/java | grep -iv \"^.*import\" | head -40; grep -rln \"OrderTotalVariation\\|PromoCodeCalculatorModule\" --include=*.java . | head"}`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/pa3/repo; grep -rn -i \"promo\" sm-shop/src/main/java sm-shop-model/src/main/java | head -40; echo ---; grep -rln \"OrderTotalVariation\\|PromoCodeCalculatorModule\\|OrderTotalPostProcessorModule\" sm-core sm-shop | head"}`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/pa3/repo; sed -n 230,275p sm-shop/src/main/java/com/salesmanager/shop/mapper/cart/ReadableShoppingCartMapper.java; grep -rn -B3 -A25 \"promo/{promo\" sm-shop/src/main/java | head -50; sed -n 1145,1175p sm-shop/src/main/java/com/`

## Approver's reply

The overall approach is right: a persisted store-scoped entity, one cart-level evaluator, re-checking the code on every cart calculation, and removing the Drools rule and the one-day expiry. But the draft still leaves the builder to choose in too many places ("for example", "preferably", "if ... or ..."). The builder sees only this file, so make every one of these choices yourself and revise design_draft.md:

1. **Spelling saved on apply (line 121).** That paragraph contradicts itself. Decide: when a shopper applies a code, look up the stored discount and save its stored `code` (the merchant's spelling) into `ShoppingCart.promoCode`. Delete the "save as entered by the shopper" wording.
2. **normalizedCode.** Normalize case only, with `toUpperCase(Locale.ROOT)`, and no trimming. A blank or missing code is 400.
3. **Date.** "Today" is `LocalDate.now()` in the JVM default zone. Use one injectable `Clock` or date supplier in both the admin defaults and the evaluator, so tests can control it. Remove the "explicitly chosen business timezone" wording.
4. **Empty promoCode.** State the exact JSON. Keep the current mapper behaviour, `promoCode: null`, and make sure no `discount` line appears in `totals`.
5. **Order totals.** Pick one approach. Mine: remove `PromoCodeCalculatorModule` from `ProcessorsConfiguration` and from `shopizer-core-ordertotal-processors.xml`, and delete `PromoCoupon.drl`. In `OrderServiceImpl.caculateShoppingCart`, call the evaluator once after the subtotal is built, add a single `OrderTotal` with code `Constants.OT_DISCOUNT_TITLE` ("discount") and the positive value, and subtract it once from the grand total. Name the exact methods and lines you'll change, and confirm that `OrderTotalServiceImpl` no longer produces any discount line per item. Also confirm that `ReadableShoppingCart.total` (or whatever the field is named) is set from that grand total.
6. **Other places that set the promo code without validating it.** The draft misses some. `ShoppingCartFacadeImpl` sets `promoCode` and `promoAdded` without validation at about lines 663-666 (`updateCartItems` with `Optional<String> promoCode`), 766-768 and 932-934 (`item.getPromoCode()` when adding items). The refresh-on-return step would drop an invalid code there, but it would also overwrite a valid existing code with an invalid one. Specify that none of these paths may overwrite `promoCode` without going through the evaluator. The simplest fix: only set it when the evaluator accepts it, and ignore it otherwise. Also list the one-day checks to remove explicitly: `OrderFacadeImpl` around lines 251-266, `ShoppingCartFacadeImpl` around 1116-1127, `ReadableShoppingCartMapper` around 113-124, and `OrderServiceImpl`.
7. **HTTP status on rejection.** `ShoppingCartApi.modifyCart` (about lines 129-143) currently wraps every exception other than `ResourceNotFoundException` in `ServiceRuntimeException`, which would turn your 400 into a 500. Say exactly how the rejection gets out as 400: rethrow your bad-request exception unwrapped, and name the existing advice/handler that maps it to 400, or the new one you add. Do the same for 409 and 404 on the admin API, naming the exception classes and handler. The success status of the promo endpoint stays 201, as today.
8. **Storing categories.** Decide: store the category codes as an `@ElementCollection` of strings, validated on write against the store's categories. At evaluation time, resolve them through `CategoryService` by store and code, then match by lineage. A category that no longer resolves is simply ignored. If none resolve, no item is eligible and the code doesn't apply.
9. **Cut scope.** Drop the "add equivalent production migration" item. Hibernate DDL is what this repo uses; just name the table names. Keep `promoAdded` as-is but unused.
10. **Unavailable items.** Say concretely which items count toward the subtotal. It must be the same set `OrderServiceImpl` already uses for the subtotal; name the condition.

Once these are revised, send it back and I'll do a final check.

## Given to the approver

The coordinator sent a message while you were working:
The agent's message:

Revised `design_draft.md` with all implementation choices made explicit, including exact validation, exception handling, promo mutation paths, totals integration, category storage, date handling, and legacy checks.

Address this before completing your current task.

- tool call `Read`: `{"file_path": "~/code/benchmark/skills-impact-work/egm-runs/pa3/repo/design_draft.md"}`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/pa3/repo; f=$(grep -rl \"class RestErrorHandler\" sm-shop/src/main/java); echo $f; grep -n -B3 \"public .*(\" $f | head -60; grep -rn \"class RestApiException\" -A5 sm-shop/src/main/java | head; grep -rn \"OT_DISCOUNT_TITLE *=\"`

## Approver's reply

The revision is much better. I checked it against the code and found four remaining issues to fix, and then I can approve.

1. **The discount line's code is wrong.** `Constants.OT_DISCOUNT_TITLE` is `"order.total.discount"`, not `"discount"` (sm-core `Constants.java:44`). `ReadableShoppingCartMapper` copies `t.getOrderTotalCode()` straight into `totals[].code`, so the cart would show the wrong code. Decide: the discount `OrderTotal` gets `orderTotalCode` = the literal `"discount"`, through a new constant such as `Constants.OT_DISCOUNT_CODE = "discount"`. Update the mapper's "no discount line, so promoCode = null" check (around lines 262-267) to use that constant. Fix the text in sections 136-148 to match. Make the test assert `code == "discount"` exactly.

2. **The XML path is wrong.** The file is `sm-core/src/main/resources/spring/processors/shopizer-core-ordertotal-processors.xml`, not `spring/shopizer-core-ordertotal-processors.xml`.

3. **Admin 400s need a concrete path.**
   - **Validation errors:** say that the discount service/facade throws `DiscountBadRequestException` (extending `RestApiException`, so it maps to 400) for every validation failure in the 400 list. Note that domain exceptions thrown in sm-core must be translated in the shop facade; name where that happens.
   - **Bad JSON values:** an unknown `"type"` or a malformed date/number fails Jackson deserialization with `HttpMessageNotReadableException`, which today falls into the generic `Exception` handler and becomes a 500. Fix it one of two ways. (a) Make the request DTO's `type`, `value`, `minimumSubtotal`, `startDate` and `endDate` fields Strings, or `type` a String, and parse them in validation. (b) Add a `RestErrorHandler` handler mapping `HttpMessageNotReadableException` to 400. Pick one; I prefer (a) for `type` plus (b) for malformed dates/numbers. State it, and add a test for an unknown type that expects 400.

4. **Conflict precedence.** If `DiscountConflictException` extends `RestApiException`, confirm that the dedicated 409 handler takes precedence. Spring picks the most specific exception type, so it should. Simplest is to make it not extend `RestApiException`. State which.

Everything else is approved as written.

## Given to the approver

The coordinator sent a message while you were working:
The agent's message:

Fixed all four remaining issues in `design_draft.md`:

- Added `Constants.OT_DISCOUNT_CODE = "discount"` and corrected mapper/order-total behavior.
- Corrected the processor XML path.
- Defined concrete 400 handling for domain validation and malformed JSON.
- Made `DiscountConflictException` a standalone runtime exception with unambiguous 409 handling.

The draft is ready for final review.

Address this before completing your current task.

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/pa3/repo; grep -n -i \"OT_DISCOUNT\\|processors/shopizer\\|HttpMessageNotReadable\\|DiscountConflictException\\|DiscountBadRequest\\|String type\\|translat\" design_draft.md"}`

## Approver's reply

APPROVED FOR BUILD
