## Given to the approver

You are a senior engineer on the shopizer team (a Java e-commerce platform). You asked for the feature below, and an AI coding agent is now designing it. Before any code is written, you review its work. Once you approve the design, a different coding agent, which sees only the approved design file, will build it.

The agent works in this checkout: ~/code/benchmark/skills-impact-work/egm-runs/pa2/repo
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

The design is ready in [design_draft.md](~/code/benchmark/skills-impact-work/egm-runs/pa2/repo/design_draft.md).

No production code was changed.

- tool call `Read`: `{"file_path": "~/code/benchmark/skills-impact-work/egm-runs/pa2/repo/design_draft.md"}`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/pa2/repo; ls; grep -rn \"promo\" --include=*.java sm-shop/src/main/java | grep -iv \"^.*import\" | head -40; grep -rln \"PromoCodeCalculatorModule\\|promoAdded\" --include=*.java --include=*.xml . | head -30"}`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/pa2/repo; grep -rln 'PromoCodeCalculatorModule\\|promoAdded\\|PromoCoupon' . | head -30; echo ---; grep -rn 'promoCode\\|PromoCode' sm-shop-model/src | head; echo ---; grep -rn 'hbm2ddl' --include='*.properties' . | head; grep -`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/pa2/repo; grep -rn 'PromoAdded\\|plusDays\\|isPromo' sm-shop/src/main sm-core/src/main | head -20; sed -n 270,320p sm-core/src/main/java/com/salesmanager/core/business/services/order/OrderServiceImpl.java; grep -n 'Discount\\|di`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/pa2/repo; sed -n 100,140p sm-shop/src/main/java/com/salesmanager/shop/mapper/cart/ReadableShoppingCartMapper.java; grep -n 'Subtotal\\|SubTotal\\|setTotal\\|setTotals\\|getTotal' sm-shop/src/main/java/com/salesmanager/shop/mappe`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/pa2/repo; sed -n 255,286p sm-shop/src/main/java/com/salesmanager/shop/mapper/cart/ReadableShoppingCartMapper.java"}`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/pa2/repo; grep -rn 'OT_DISCOUNT_TITLE\\s*=' sm-*/src/main; sed -n 80,115p sm-core/src/main/java/com/salesmanager/core/business/modules/order/total/PromoCodeCalculatorModule.java; grep -rn 'Exception' sm-shop/src/main/java/com/sa`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/pa2/repo; sed -n 20,110p sm-shop/src/main/java/com/salesmanager/shop/store/api/exception/RestErrorHandler.java; grep -rn 'CONFLICT' sm-shop/src/main/java | head -5; grep -n 'promo' sm-shop/src/main/java/com/salesmanager/shop/sto`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/pa2/repo; sed -n 115,150p sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/shoppingCart/ShoppingCartApi.java"}`

## Approver's reply

Good overall shape: one evaluate() service, reconcile on every cart read, and store-scoped repositories. Before I can approve, several points are either left open ("either/or", "or equivalent", "decide separately") or would come out wrong against this code. The builder sees only the design file, so please settle each of these in design_draft.md:

1. **The discount line code must be literally "discount".** Today the module emits `Constants.OT_DISCOUNT_TITLE` = "order.total.discount", and the mapper copies `getOrderTotalCode()` straight into `totals[].code`. Say exactly what the cart JSON line will carry ("discount") and where that happens. Also update the mapper's check (ReadableShoppingCartMapper ~line 263), which looks for OT_DISCOUNT_TITLE to decide whether to null out promoCode.

2. **Subtotal convention: pick one, and here it is.** At OrderServiceImpl ~line 293, `subTotal = subTotal.subtract(variation.getValue())`, and the mapper sends `orderSummary.getSubTotal()` back as the cart's "subtotal". If you keep that, the response "subtotal" becomes the post-discount amount, which breaks "total = subtotal − discount". Decision: the discount OrderTotal holds a positive value. `summary.getSubTotal()` and the "subtotal" totals line stay the pre-discount item subtotal. The grand total subtracts the discount exactly once. Checkout/order creation (OrderFacadeImpl, OrderServiceImpl) uses this same pipeline. Drop the "decide and document the order snapshot separately" sentence. The order's persisted totals are whatever this pipeline produces.

3. **Compute once per cart.** PromoCodeCalculatorModule currently runs per item and multiplies the item price by a Drools factor. State that the discount is computed once per cart through evaluate(), giving at most one discount OrderTotal, never one per item. Delete PromoCoupon.drl and its rule wiring (ProcessorsConfiguration / KieSession for the promo) rather than leaving them in place.

4. **Error mapping must be concrete. The existing handler won't give these statuses as-is.**
   - There is no 409 handler today. Add a specific exception (e.g. `ConflictException`) plus a `@ResponseStatus(CONFLICT)` handler in RestErrorHandler.
   - `handleServiceException(ServiceRuntimeException)` and the generic `Exception` handler dereference `getCause()` and will NPE when the cause is null. Make the 400 path for validation errors and for "code does not apply" null-safe, or use an exception/handler that doesn't need a cause.
   - Malformed input must give 400, not 500. That covers an unknown "type" (don't bind it straight to an enum, or handle HttpMessageNotReadableException as 400), a bad date string, and a non-numeric value. Say how: e.g. type as a String DTO field validated in the service, and dates parsed as "yyyy-MM-dd" strings, or with the JSR-310 module confirmed present.
   - Today the promo endpoint wraps every exception in `new ServiceRuntimeException(e)`. Make sure the "does not apply" rejection reaches the client as 400.

5. **Remove the hedges.**
   - The controller lives at `com.salesmanager.shop.store.api.v1.discount.DiscountApi`.
   - DELETE returns 200 with an empty body.
   - Promo success keeps its current 201.
   - "Today" means `LocalDate.now()` from a single injectable `Clock` bean (system default zone). No store-timezone lookup.
   - Schema comes from the JPA mapping (hbm2ddl=update in all profiles, create in tests), so drop the "if migrations…" branch.

6. **promoCode when nothing applies:** null, per the existing mapper convention. Say so explicitly.

7. **Smaller fixes:**
   - The mapper's promoCode must come from the reconciled evaluation, i.e. the stored merchant spelling.
   - The one-day check sites are ReadableShoppingCartMapper ~114, ShoppingCartFacadeImpl ~1117, OrderFacadeImpl ~253 and OrderServiceImpl ~437. Remove them all.
   - The `setPromoAdded(new Date())` calls at ShoppingCartFacadeImpl 666/768/934/1156 must not re-apply or refresh a code that no longer applies.
   - Remove "category codes should be de-duplicated…" unless it is trivial. It isn't required, and response order isn't specified.

Send the revised design when it's done.

## Given to the approver

The coordinator sent a message while you were working:
The agent's message:

The revised design is complete in [design_draft.md](~/code/benchmark/skills-impact-work/egm-runs/pa2/repo/design_draft.md), with all requested decisions made explicit.

Address this before completing your current task.

- tool call `Read`: `{"file_path": "~/code/benchmark/skills-impact-work/egm-runs/pa2/repo/design_draft.md"}`

## Approver's reply

Nearly there. Two small fixes, then I'll approve:

1. Line 38 still says `startDate` defaults to "the current date in the store's business timezone". That contradicts line 76. Change it to `LocalDate.now(clock)` (system-default zone), as line 76 says.
2. The validation list in "Validation rules" runs straight into the BigDecimal/Clock paragraph with no blank line. Add the line break so the last bullet and the paragraph are separate.

Nothing else changes.

## Given to the approver

The coordinator sent a message while you were working:
The agent's message:

Both requested fixes are complete in `design_draft.md`.

Address this before completing your current task.

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/pa2/repo; grep -n 'timezone\\|clock' design_draft.md; sed -n 70,80p design_draft.md"}`

## Approver's reply

APPROVED FOR BUILD
