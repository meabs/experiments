## Given to the approver

You are a senior engineer on the shopizer team (a Java e-commerce platform). You asked for the feature below, and an AI coding agent is now designing it. Before any code is written, you review its work. Once you approve the design, a different coding agent, which sees only the approved design file, will build it.

The agent works in this checkout: ~/code/benchmark/skills-impact-work/egm-runs/ea1/repo
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

The drafting workflow is ready. Please confirm whether I should begin writing the first section to [`design_draft.md`](~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/design_draft.md).

## Approver's reply

Yes, go ahead and write the first section to design_draft.md. Keep each section concrete and tied to the real code: name the classes, files and methods you will add or change, because the builder will see only this file. Across the design, make sure you cover these points:
- the data model, the migration and the case-insensitive per-store uniqueness;
- the admin endpoints and how they are protected and scoped by ?store=;
- validation, mapped to the exact 400 and 409 cases;
- how the discount is applied and recalculated every time the cart is returned (including the category subtree, rounding HALF_UP to 2 decimal places, and the AMOUNT cap);
- how the existing Test1234 rule and the one-day expiry are removed;
- what happens to the cart's previous code when an apply is rejected.

Send me each section when it is done.

## Given to the approver

The coordinator sent a message while you were working:
The agent's message:

The initial section is drafted in [`design_draft.md`](~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/design_draft.md).

It covers the current code paths, persisted store-scoped discounts, CRUD and validation goals, recalculation rules, category handling, rounding, previous-code behavior, and removal of `Test1234` and one-day expiry.

Please review it. Should I proceed with the Technical Plan section?

Address this before completing your current task.

- tool call `Read`: `{"file_path": "~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/design_draft.md"}`

## Approver's reply

The overview is mostly right. Please fix these points before you move on, then go ahead with the Technical Plan:

1. Line 28 says "If the persisted code no longer applies, the cart is cleared." That must mean only the promo code is cleared (promoCode empty, no discount line). The cart's items must never be touched. Please reword it.
2. Goals: say explicitly that 409 also covers a PUT that renames a code to one that already exists in the store, compared ignoring case. A PUT that keeps the code's own name, or changes only its case, is not a conflict.
3. Goals: state what happens with an {id} that does not exist or belongs to another store on PUT/DELETE. It should be 404, and a store must never be able to read, change or delete another store's codes.
4. A shopper code that does not apply must give 400 in every case: unknown code, another store's code, inactive, outside its dates, below the minimum, or no eligible items. Say this outright.
5. Say which date counts as "today" (server local date via LocalDate.now() is fine, as long as you use it the same way everywhere), and that both start and end dates are inclusive.

For the Technical Plan, name the concrete entity, table and migration, repository, service, controller, DTOs and exception-to-status mapping. Also cover the exact cart read paths where the recalculation happens and how it reaches `totals`, `subtotal` and `total`, and what you remove from the drl, the module and the promoAdded expiry. Keep to existing project conventions, for example how other private APIs check store admin rights.

## Given to the approver

The coordinator sent a message while you were working:
The agent's message:

I revised the overview and goals, then added the Technical Plan to [`design_draft.md`](~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/design_draft.md).

The updates cover the requested status codes, store isolation, date semantics, cart-preserving failure behavior, persistence model, APIs, recalculation paths, totals, category traversal, rounding, migration, and removal of the legacy rule/expiry.

Please review both sections. Should I proceed with Alternatives Considered?

Address this before completing your current task.

- tool call `Read`: `{"file_path": "~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/design_draft.md"}`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/ea1/repo; ls sm-core/src/main/resources/ | head; grep -rl -i \"flyway\" --include=pom.xml --include=*.properties --include=*.yml . | head; grep -rn \"hbm2ddl\\|ddl-auto\" --include=*.properties --include=*.yml --include=*.xml . `

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/ea1/repo; grep -rli \"flyway\" --include='pom.xml' --include='*.properties' --include='*.yml' . | head; grep -rn \"hbm2ddl\\|ddl-auto\" --include='*.properties' --include='*.yml' --include='*.xml' . | head; grep -rn \"PromoCodeC`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/ea1/repo; sed -n 95,175p sm-shop/src/main/java/com/salesmanager/shop/mapper/cart/ReadableShoppingCartMapper.java; sed -n 425,460p sm-core/src/main/java/com/salesmanager/core/business/services/order/OrderServiceImpl.java; grep -n`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/ea1/repo; sed -n 60,130p sm-core/src/main/java/com/salesmanager/core/business/modules/order/total/PromoCodeCalculatorModule.java; sed -n 460,560p sm-core/src/main/java/com/salesmanager/core/business/services/order/OrderServiceIm`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/ea1/repo; grep -rn \"OT_DISCOUNT_TITLE\\s*=\" --include='*.java' .; grep -n \"OrderTotalPostProcessorModule\\|getValue()\\|subtract\\|caculateProductPiceVariation\\|discount\" sm-core/src/main/java/com/salesmanager/core/business`

## Approver's reply

The Overview and Goals are good now. The Technical Plan needs these changes before you go on to Alternatives:

1. **There is no Flyway in this repo.** The runtime profiles use `hibernate.hbm2ddl.auto=update` and the tests use `create`. Drop `db/migration/V20261023__...sql` and the edit to `create_schema.sql`. The schema should come from the JPA entities: use a `@Table(uniqueConstraints=...)` on the merchant plus a normalized code column, such as a `CODE_NORMALIZED` column that holds the uppercased code. Hibernate can create that constraint, which a functional `lower()` index cannot be. Keep the service-level check and still translate `DataIntegrityViolationException` to 409.

2. **Totals pipeline.** Be precise here, because this is where the builder will go wrong. Today the discount arrives as an `OrderTotalPostProcessorModule` (`PromoCodeCalculatorModule.caculateProductPiceVariation`). It is called per item inside `OrderServiceImpl.caculateOrder`, which subtracts it from `subTotal` (around line 293). The code is `Constants.OT_DISCOUNT_TITLE` = "order.total.discount". The request needs all of the following:
   - `totals` has a line whose code is exactly `"discount"`, with a positive value. Say whether you change the constant or set the code explicitly, and check what else uses `OT_DISCOUNT_TITLE`.
   - `subtotal` is the full pre-discount subtotal.
   - `total` = subtotal − discount.
   - The discount is computed once per cart over the eligible items. It must not be computed per item, and the per-item percentage of `calculateProductPrice` must not be used.
   Spell out exactly where in `OrderServiceImpl.caculateShoppingCart`/`caculateOrder` the new `DiscountCalculationService` is called, and how the subtotal, total and totals list are built. Say what happens to `PromoCodeCalculatorModule`: either remove it from the post-processor list, or rewrite it to delegate. Pick one.
   - The minimum-subtotal check and the eligible subtotal must use the same item set and prices as the cart's displayed subtotal. Today's code filters out unavailable products, so say how you handle that.

3. **Where recalculation happens.** `ReadableShoppingCartMapper.merge` already calls `shoppingCartCalculationService.calculate` and nulls `promoCode` when no discount line is present. Build on that. Name every place that sets `promoCode` on the response today and the one place it will be set from now on: `ShoppingCartFacadeImpl` around line 1116 has its own expiry copy. Also say how the cleared code gets persisted: at the line 436 expiry block in `OrderServiceImpl`, or elsewhere. Make sure a code that is cleared stays cleared, so that if the merchant later fixes the code the cart does not pick it up again.

4. **Other ways a code gets onto the cart.** `ShoppingCartFacadeImpl` lines ~766 and ~932 copy `PersistableShoppingCartItem.promoCode` into the cart without any validation, and line ~1156 is also a setter. Every path that sets a code must either go through the same validation as the promo endpoint, or be ignored. Say which you choose for each one.

5. **Category descendants.** Say concretely how you work them out. `Category` has `lineage` and `getParent()`. One option is to resolve each restricted category code for the store, then treat a product category as eligible if it equals one of them or its lineage contains `/<id>/`. Check the real lineage format in the code and write it down.

6. **Admin authorization.** Name the exact group constants and the `UserFacade` calls you copy, and cite the controller you copy them from. Also say that an empty or blank `categories` list means "no restriction".

7. **Validation detail.**
   - Is an unknown `type` string a 400 even when Jackson fails to bind the enum? Make sure deserialization errors map to 400, not 500. The simplest way is a String field validated in the service.
   - A blank code is the same as a missing one.
   - If `endDate` is given without `startDate`, check it against today.

Fix these, then go ahead with Alternatives Considered. Keep that section short.

## Given to the approver

The coordinator sent a message while you were working:
The agent's message:

The Technical Plan has been corrected and Alternatives Considered added in [`design_draft.md`](~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/design_draft.md).

The updates cover the JPA-only schema, normalized uniqueness, exact totals pipeline, cart recalculation and persistence behavior, every promo setter, category lineage, authorization groups, and all validation/binding cases.

Please review these sections. Should I proceed to Detailed Implementation?

Address this before completing your current task.

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/ea1/repo; awk '/^## Technical Plan/,0' design_draft.md", "description": "Show Technical Plan onward"}`

## Approver's reply

This is a good revision. Go ahead with Detailed Implementation, and fold these small points in:

1. **Products with several categories.** A product can belong to several categories. An item is eligible if any one of its product's categories matches a selected category or is below one in the lineage. State this explicitly.
2. **Category deleted after the code was saved.** If a restricted category code no longer resolves when the cart is calculated, skip that code. That must not cause an error. If none of the restricted categories resolve, nothing is eligible, so the code does not apply.
3. **Scope of the 400 binding handler.** Don't change global behaviour for other APIs. Put the `HttpMessageNotReadableException` and binding-to-400 handling only on `DiscountCodeApi`, as a controller-local `@ExceptionHandler` or a `@ControllerAdvice(assignableTypes = DiscountCodeApi.class)` with higher precedence. Leave `RestErrorHandler` as it is apart from the two new discount exceptions.
4. **Shopper lookup.** The shopper lookup uses `CODE_NORMALIZED`, uppercased the same way as on save (`toUpperCase(Locale.ROOT)`). The response `promoCode` is always the stored merchant-written `CODE`, never the shopper's input.
5. **Rounding of PERCENT values.** For PERCENT, compute eligibleSubtotal × value / 100 at full precision, then round once with `setScale(2, HALF_UP)`. Don't round the intermediate value/100 step.

In Detailed Implementation, include a concrete test plan. It must cover:
- admin CRUD: 201 with id, list, PUT, DELETE, 404 for a foreign or unknown id, 409 on create and on rename ignoring case, and the same code allowed in two stores;
- each 400 validation case;
- applying a code: percent and amount, the amount cap, HALF_UP rounding (for example a .xx5 case), category subtree eligibility, minimum subtotal, inclusive start and end dates, inactive, and another store's code;
- a rejected apply keeps the previous code, and a successful apply replaces it;
- the code is dropped after items are removed, or the code is deactivated, edited or deleted;
- Test1234 gives no discount;
- the response shape: `promoCode`, the `totals` line with code `discount`, `subtotal`, and `total`.

Also list the files you add and change.

## Given to the approver

The coordinator sent a message while you were working:
The agent's message:

The Detailed Implementation section is complete in [`design_draft.md`](~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/design_draft.md).

It includes all files to create or modify, implementation rationale, exact cart/totals behavior, authorization and validation handling, legacy cleanup, and the requested comprehensive test plan.

Please review it and tell me whether revisions are needed or the draft is ready for finalization.

Address this before completing your current task.

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/ea1/repo; awk '/^## Detailed Implementation/,0' design_draft.md; grep -n \"any one of\\|skip\\|Locale.ROOT\\|assignableTypes\\|full precision\" design_draft.md", "description": "Show Detailed Implementation section"}`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/ea1/repo; find . -name ResourceNotFoundException.java -o -name RestErrorHandler.java | grep -v target; ls sm-core/src/main/java/com/salesmanager/core/business/exception/", "description": "Locate exception classes"}`

## Approver's reply

This is nearly ready. One structural problem needs fixing before I can approve it: module dependencies.

`sm-core` cannot depend on `sm-shop` or `sm-shop-model`. Right now the plan has a few things the wrong way round:
- `DiscountCodeServiceImpl` in sm-core "validates the DTO" (the DTOs are in sm-shop-model);
- it throws `ResourceNotFoundException`, `DiscountValidationException` and `DiscountConflictException`, which are all in `sm-shop/.../store/api/exception/`;
- `DiscountCalculationService` in sm-core is meant to produce the shopper 400.

Please restructure it this way. Name the files and the exact exception or result types you use.

1. **sm-core, `DiscountCodeService`.** It works only on the `DiscountCode` entity and `MerchantStore`, with no DTOs and no sm-shop exceptions. It signals outcomes with core types: either new exceptions in sm-core (for example `com.salesmanager.core.business.exception` or the existing core exception package, so check where `ServiceException` lives) or return values. The sm-core service can do the store-scoped lookup and the normalized-uniqueness check. The DTO checks (missing or blank code or value, an unknown type string, value ranges, dates, categories) can go either in a new sm-shop `DiscountCodeFacade` or in the core service working on the entity. Pick one place and say which.
2. **sm-shop, new `DiscountCodeFacade`/`DiscountCodeFacadeImpl`** (under `store/controller/...` or `store/facade/...`, following existing facade conventions). It maps DTO ↔ entity, applies the defaults, and translates core outcomes into `ResourceNotFoundException` (404), `DiscountConflictException` (409) and `DiscountValidationException` (400). `DiscountCodeApi` calls only the facade.
3. **Shopper apply.** `DiscountCalculationService` (sm-core) returns a result saying either "not applicable" or "applied with an amount". It does not throw an HTTP-specific exception. `ShoppingCartFacadeImpl.modifyCart` (sm-shop) turns "not applicable" into `DiscountValidationException` (400). Check what the promo endpoint in `ShoppingCartApi` does today with exceptions from `modifyCart`, so the 400 actually reaches the client and isn't swallowed or turned into another status. Say what you found.

Update the file list and the Technical Plan to match. After that I expect to approve.

## Given to the approver

The coordinator sent a message while you were working:
The agent's message:

The module-boundary revision is complete in [`design_draft.md`](~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/design_draft.md).

`sm-core` now uses only core entities, stores, and core exceptions/results. DTO mapping, validation, defaults, and HTTP exception translation are owned by the new shop-layer `DiscountCodeFacade`. Shopper non-application uses a core `DiscountApplicationResult`, with `ShoppingCartFacadeImpl` translating it to HTTP 400 while preserving the endpoint’s existing exception flow.

The file list and implementation responsibilities have been updated accordingly.

Address this before completing your current task.

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/ea1/repo; grep -n -i \"facade\\|DiscountApplicationResult\\|ShoppingCartApi\\|core exception\\|ServiceException\\|swallow\\|catch\" design_draft.md | head -60; grep -n \"promo\" -A25 sm-shop/src/main/java/com/salesmanager/shop/s`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/ea1/repo; sed -n 215,232p design_draft.md; sed -n 420,432p design_draft.md", "description": "Read promo endpoint exception handling text"}`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/ea1/repo; grep -n \"ShoppingCartApi.java\\|^#### \" design_draft.md", "description": "List file entries in design"}`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/ea1/repo; find . -name ServiceException.java -not -path '*/target/*'", "description": "Locate ServiceException"}`

## Approver's reply

The module boundaries look right now. The core exceptions live beside `ServiceException` in sm-core-model, and the facade owns the DTO and HTTP translation.

There is one gap left. The Technical Plan says the promo endpoint's catch block must explicitly rethrow `DiscountValidationException`, but `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/shoppingCart/ShoppingCartApi.java` is not in the Target Files list. Please add it as a Modify entry. In `modifyCart(@PathVariable String code, @PathVariable String promo, ...)` (the `POST /cart/{code}/promo/{promo}` handler), rethrow `DiscountValidationException` unchanged alongside `ResourceNotFoundException`. Also add a test assertion that a non-applying code returns exactly 400 through this endpoint.

Once that is in, I'll approve.

## Given to the approver

The coordinator sent a message while you were working:
The agent's message:

Added the missing `ShoppingCartApi.java` implementation entry.

The plan now explicitly rethrows `DiscountValidationException` unchanged from the promo endpoint and tests that non-applying codes return exactly HTTP 400 through that endpoint.

Address this before completing your current task.

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/ea1/repo; grep -n -A6 \"ShoppingCartApi.java\" design_draft.md; grep -n \"exactly.*400\\|400.*promo endpoint\" design_draft.md", "description": "Verify ShoppingCartApi entry added"}`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/ea1/repo; grep -n \"400\" design_draft.md | tail -8", "description": "Check test plan mentions of 400"}`

## Approver's reply

APPROVED FOR BUILD

## Given to the approver

The coordinator sent a message while you were working:
The design draft you approved is now going through EGM's review, in which fresh reviewers with no conversation history read the design. The agent's message:

Stage 5 is complete. Findings are in [`zoom_out_report.md`](~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/zoom_out_report.md).

Choose one:

1. Proceed to Stage 6 (Comprehension Test)
2. Update the document first and rerun Stage 5
3. Pause review

Address this before completing your current task.

- tool call `Read`: `{"file_path": "~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/zoom_out_report.md"}`

## Approver's reply

Option 2: update the document, then rerun Stage 5. All four findings are valid. Resolve them as follows.

1. **Calculation context.** `DiscountCalculationService.evaluate` takes `(MerchantStore store, String code, List<ShoppingCartItem> pricedItems, LocalDate today)`. `pricedItems` is the unavailable-product-filtered list that `OrderServiceImpl` already prices. The eligible subtotal and the minimum check use each item's already-computed line subtotal (item price × quantity, the same value shown as the cart subtotal). The service must not re-price anything. For the apply endpoint, `ShoppingCartFacadeImpl.modifyCart` gets the same items and prices by running the cart through the existing calculation path first, or through a shared helper in `OrderServiceImpl`/`ShoppingCartCalculationService`. Name which one, so there is exactly one pricing path.

2. **Canonical code.** Do both:
   - (a) On a successful apply, persist the stored merchant `CODE` (not the shopper's input) to `ShoppingCart.promoCode`.
   - (b) Carry the result's canonical code through `OrderTotalSummary`, for example as a new `promoCode` field or the `discount` OrderTotal's `text`. The mapper sets the response `promoCode` from that, and only when a discount line exists.

   That way, if the merchant later changes only the case of the code, the cart shows the current spelling.

3. **Total arithmetic.** Subtract the discount from the merchandise subtotal before any shipping or tax:
   - `subTotal` = full pre-discount item subtotal (unchanged meaning);
   - discount line = positive value;
   - any tax is computed on (subTotal − discount), if the existing tax module is easy to feed. If it isn't, keep tax as it is today and say so;
   - `total` = subTotal − discount + shipping + tax.

   For a cart with no shipping or tax lines, which is the normal cart response, this gives total = subtotal − discount exactly. State the order of operations in `caculateOrder` explicitly.

4. **Nit.** Set `codeNormalized` in a `@PrePersist`/`@PreUpdate` callback on `DiscountCode` (`code.toUpperCase(Locale.ROOT)`), and add a unit test for it.

Update the document, then rerun Stage 5.

## Given to the approver

The coordinator sent a message while you were working:
The agent's message:

Stage 5 rerun is complete. Findings are in [`zoom_out_report.md`](~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/zoom_out_report.md).

Choose one:

1. Proceed to Stage 6 (Comprehension Test)
2. Update the document first and rerun Stage 5
3. Pause Review

Address this before completing your current task.

- tool call `Read`: `{"file_path": "~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/zoom_out_report.md"}`

## Approver's reply

Option 2: update the document and rerun Stage 5. Resolve the two findings as follows.

1. **Dependency cycle.** Don't add the helper to `ShoppingCartCalculationService`. Put `preparePricedAvailableItems(ShoppingCart, MerchantStore, Language)` on `OrderService`/`OrderServiceImpl` as a public method, and have `caculateShoppingCart` use it internally. `ShoppingCartFacadeImpl.modifyCart` calls `orderService.preparePricedAvailableItems(...)`, then `discountCalculationService.evaluate(...)`. `OrderServiceImpl` depends on `DiscountCalculationService`, and `DiscountCalculationService` depends only on the repository and `CategoryService`. It must not depend on `OrderService` or `ShoppingCartCalculationService`. That gives no cycle. Write the dependency direction into the document.

2. **Ordering with other variations.** Leave the existing `OrderTotalVariation` modules (for example the manufacturer shipping module) as they are. They keep adjusting `subTotal` exactly as today. The merchant discount comes after them:
   - eligibility, the minimum check and the eligible subtotal use the items' line subtotals (price × quantity), not the variation-adjusted value;
   - the discount is capped so it never exceeds the summary `subTotal` after variations, so the total never goes negative;
   - the discount is not subtracted from `subTotal`. Instead, `total` = `subTotal` (as produced today, after any legacy variations) − merchant discount + shipping + tax.

   State this as an invariant: the response `total` = `subtotal` − the `discount` line value + shipping + tax. With no other variations, shipping or tax, that is exactly `subtotal` − `discount`. The merchant discount is never routed through the post-processor/variation list.

Update the document, then rerun Stage 5.

## Given to the approver

The coordinator sent a message while you were working:
The agent's message:

Stage 5 rerun 2 is complete. Findings are in [`zoom_out_report.md`](~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/zoom_out_report.md).

Choose one:

1. Proceed to Stage 6 (Comprehension Test)
2. Update the document first and rerun Stage 5
3. Pause Review (save progress and exit)

Address this before completing your current task.

- tool call `Read`: `{"file_path": "~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/zoom_out_report.md"}`

## Approver's reply

Option 1. Proceed to Stage 6, but first make these two small edits to the document. There is no need to rerun Stage 5 for them.

1. **No saved code.** If `promo` is null or blank, `evaluate` returns `DiscountApplicationResult.notApplicable()` straight away, before normalizing it or looking anything up. In that case `caculateShoppingCart` does not save the cart and adds no discount line. The cart is only cleared and saved when a non-blank saved code fails to apply. On the apply endpoint, `modifyCart` with a blank promo is a 400, as before.

2. **Discount that rounds to zero.** Applicability is decided only by the rules in the request: store, active, dates, minimum, and at least one eligible item. The size of the discount is not part of that. If a code applies but the discount rounds to `0.00`, it still applies: `promoCode` is shown and the `discount` line is present with value `0.00`. "Positive" in the contract means the line uses a non-negative sign convention. It is never negative. Add a unit test for this.

## Given to the approver

The coordinator sent a message while you were working:
The agent's message:

Stage 6 is complete. Findings are in [`comprehension_report.md`](~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/comprehension_report.md).

Choose one:

1. Proceed to Stage 7 (Critic Review)
2. Update the document first and rerun Stage 6
3. Pause Review

Address this before completing your current task.

- tool call `Read`: `{"file_path": "~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/comprehension_report.md"}`

## Approver's reply

Option 2: update the document, then rerun Stage 6. Here are my decisions on each finding.

1. **Mapper wording.** Set `promoCode` whenever a `discount` line exists, with any value of 0 or more. Remove the "positive" condition everywhere it appears.

2. **Category collection.** Map the categories as `@ElementCollection` `Set<String> categories` with `@CollectionTable(name="DISCOUNT_CODE_CATEGORY", joinColumns=@JoinColumn(name="DISCOUNT_CODE_ID"))` and `@Column(name="CATEGORY_CODE")`.
   - The `DiscountCode` entity owns the table.
   - A PUT replaces the set in place (`clear()` and then `addAll`).
   - Deleting the entity removes its rows. JPA handles this for element collections.

3. **DTO rules.**
   - `code`: required, not blank, at most 100 characters (`CODE` and `CODE_NORMALIZED` are both 100). Store it as written; don't trim it.
   - `value`: required and greater than 0. A PERCENT value must also be 100 or less.
   - `minimumSubtotal`: optional, and must be 0 or more when present. A negative value is a 400.
   - Store `value` and `minimumSubtotal` in `DECIMAL(19,4)` columns. Don't add extra rules about scale.
   - `categories`: optional. A null or empty list means no restriction. A blank entry or an unknown category code is a 400. Duplicate entries are collapsed by the Set.
   - PUT is a full replacement. Optional fields that are left out become null or their defaults (`active=true`, `startDate=today`), exactly as on create.

4. **Exception path.** Put the new core exceptions in `sm-core-model/src/main/java/com/salesmanager/core/business/exception/`, next to `ServiceException`. Fix the architecture section to say the same.

5. **`caculateOrder`.** Don't change its signature. Have `caculateOrder` itself evaluate the discount when `OrderSummary.getPromoCode()` is not blank. It calls `DiscountCalculationService.evaluate` with `summary.getProducts()` (already filtered and priced) once the line subtotals are computed. That gives a single path for both the cart and checkout calculation, with no extra context to thread through.
   - `caculateShoppingCart` sets `orderSummary.setPromoCode(cart.getPromoCode())`.
   - After calculating, `caculateShoppingCart` checks whether the returned `OrderTotalSummary` has a `discount` line. If the cart had a code and there is no `discount` line, it clears the code and saves the cart.
   - The order/checkout path in `OrderFacadeImpl` keeps passing the cart's code into `OrderSummary`, as it does today minus the expiry check, so checkout totals match the cart.

6. **Product and category data.** `DiscountCalculationServiceImpl.evaluate` runs inside a `@Transactional(readOnly = true)` boundary and reads `item.getProduct().getCategories()`. An item whose product is null, or has no categories, is not eligible under a category restriction. It still counts toward the minimum subtotal and is still eligible when there is no restriction. If lazy loading is a problem in tests, load the product's categories through the existing `CategoryService`/`ProductService` by product id. Name the method you would use.

7. **Store resolution.** Keep the existing behaviour of the `@ApiIgnore MerchantStore` argument resolver used by all private APIs. Note this in one line and add nothing new.

## Given to the approver

The coordinator sent a message while you were working:
The agent's message:

Stage 6 rerun is complete. Findings are in [`comprehension_report.md`](~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/comprehension_report.md).

Choose one:

1. Proceed to Stage 7 (Critic Review)
2. Update the document first and rerun Stage 6
3. Pause Review (save progress and exit)

Address this before completing your current task.

- tool call `Read`: `{"file_path": "~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/comprehension_report.md"}`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/ea1/repo; grep -rn \"authorizedStore\\|userInRoles\\|authorizedGroup\" sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/category/CategoryApi.java sm-shop/src/main/java/com/salesmanager/shop/store/controller/user/facade/U`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/ea1/repo; grep -rn \"authorizedStore\\|userInRoles\\|authorizeStore\" --include='*.java' sm-shop/src/main/java | head -8", "description": "Find store-level authorization helpers"}`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/ea1/repo; sed -n 645,690p sm-shop/src/main/java/com/salesmanager/shop/store/facade/user/UserFacadeImpl.java; sed -n 25,50p sm-shop/src/main/java/com/salesmanager/shop/utils/AuthorizationUtils.java", "description": "Read authoriz`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/ea1/repo; grep -n -B3 \"@DeleteMapping\" sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/category/CategoryApi.java; grep -n -A2 \"@DeleteMapping\" sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/category/Catego`

## Approver's reply

Option 2: update the document, then rerun Stage 6. My decisions:

1. **Per-store authorization.** Two existing layers already handle this. Write both into the document:
   - (a) `MerchantStoreArgumentResolver` calls `userFacade.authorizeStore(store, requestURI)` for every `/private/` path. That throws `ResourceNotFoundException` for an unknown store. It allows the request only when the user's merchant equals the `?store=` code, or when the user is in `GROUP_SUPERADMIN`.
   - (b) Inside each `DiscountCodeApi` method, call `AuthorizationUtils.authorizeUser(authenticatedUser, roles, merchantStore)` (sm-shop `utils/AuthorizationUtils`). `authenticatedUser` comes from `authorizationUtils.authenticatedUser()`. The roles are GROUP_SUPERADMIN, GROUP_ADMIN, GROUP_ADMIN_CATALOGUE and GROUP_ADMIN_RETAIL. This checks the group, and also checks store membership for anyone who is not a superadmin. A superadmin may manage any store's codes.
   - Add an integration test: an admin of store A calling with `?store=B` gets rejected.

2. **`DiscountApplicationResult.total`.** Remove that field. The result carries only `applicable`, the canonical `code`, `eligibleSubtotal` and `discount`. `OrderServiceImpl.caculateOrder` alone computes the totals.

3. **CRUD responses.**
   - POST: 201 with the `ReadableDiscountCode`.
   - GET: 200 with a JSON array of `ReadableDiscountCode`, ordered by id ascending, no pagination.
   - PUT: 200 with the updated `ReadableDiscountCode`.
   - DELETE: 200 with an empty body (`@ResponseStatus(OK)`, void), matching `CategoryApi.delete`.
   - A later GET or PUT/DELETE on a deleted id gives 404.

## Given to the approver

The coordinator sent a message while you were working:
The agent's message:

Stage 6 rerun 2 is complete. Findings are in [`comprehension_report.md`](~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/comprehension_report.md).

Choose one:

1. Proceed to Stage 7 (Critic Review)
2. Update the document first and rerun Stage 6
3. Pause Review (save progress and exit)

Address this before completing your current task.

- tool call `Read`: `{"file_path": "~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/comprehension_report.md"}`

## Approver's reply

Option 2: update the document, then rerun Stage 6. My decisions:

1. **Deleted-ID GET.** Remove the claim about GET on a deleted id. There is no `GET /discounts/{id}`, and you must not add one. After a DELETE, the code is missing from the list GET, and a PUT or DELETE on that id returns 404.

2. **Uniqueness translation.** The core `DiscountCodeServiceImpl` turns `DataIntegrityViolationException` into the core `DiscountCodeConflictException` and does nothing more. The shop `DiscountCodeFacadeImpl` turns `DiscountCodeConflictException` into the shop `DiscountConflictException`, and that gives HTTP 409. Correct the persistence section to say this.

3. **Invalid-cart sequence.** There is one calculation and one evaluation. In `caculateOrder`, when the evaluator returns not-applicable, the order totals simply have no discount line, so the summary it builds already has no discount. `caculateShoppingCart` returns that same summary as it is, with no second calculation. Before returning, if the cart's saved `promoCode` was not blank and the summary has no `discount` line, it sets `ShoppingCart.promoCode` to null and calls `shoppingCartService.saveOrUpdate(cart)`. That is the only place the cleared code is persisted.

## Given to the approver

The coordinator sent a message while you were working:
The agent's message:

Stage 6 rerun 3 is complete. The report is in [`comprehension_report.md`](~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/comprehension_report.md).

Choose one:

1. Proceed to Stage 7 (Critic Review)
2. Update the document first and rerun Stage 6
3. Pause Review (save progress and exit)

Address this before completing your current task.

- tool call `Read`: `{"file_path": "~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/comprehension_report.md"}`

## Approver's reply

Option 1: proceed to Stage 7, the Critic Review.

## Given to the approver

The coordinator sent a message while you were working:
The agent's message:

Stage 7 is complete. Findings are in [`critic_report.md`](~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/critic_report.md).

Choose one:

1. Proceed to Stage 8 (Intermediate Zoom Out Review)
2. Resolve findings with an agent
3. Update the document manually and rerun Stage 7
4. Pause Review

Address this before completing your current task.

- tool call `Read`: `{"file_path": "~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/critic_report.md"}`

## Approver's reply

Make the edits below yourself; do not hand them to another agent. Then go to Stage 8 without rerunning Stage 7. Most of these findings would add scope that the request does not ask for.

**Fix these:**
1. **Minimum-subtotal basis.** The request says "the cart's subtotal is at least its minimum". So the minimum is checked against the whole cart subtotal, meaning the line subtotals of all filtered, priced items. It is not checked against the eligible subtotal. Add an example to the document: a cart with shoes 60 and hats 50, and a code limited to shoes with a minimum of 100. The code applies (110 ≥ 100), and the discount is worked out on the 60. Add this as a test case too.
2. **Style: wording.** Use "discount code" for the merchant's record, "promo input" for what the shopper sends, and "category code" for categories. Replace "restricted code" wherever it means a category code.
3. **Style: line numbers and vague references.** Replace every "around line N" with the method name. Name the concrete processor Spring configuration file and the facade pattern you are copying, giving the actual class names.
4. **Style: the exception paragraph.** Fix the malformed fragment there, and the informal status phrasing.
5. **Tax.** State the choice in one sentence. Tax stays on the existing tax module's base, unchanged by this feature. Keep the invariants already stated: the discount is never negative, the discount is capped at the post-variation subTotal, and the total is never negative.

**Decline these, and note each in one line under Non-Goals or a short "Constraints" note:**
- Schema migration/backfill/rollback. The repo uses hbm2ddl and these are brand-new tables with no legacy data.
- Pagination and limits on the admin list, and bulk category prefetch. Out of scope; the per-store code volume is small.
- A clock abstraction or timezone configuration. Server-local `LocalDate.now()` is the decided rule. If it fits with no extra work, you may inject a `java.time.Clock` bean for tests, but it is not required.
- Optimistic locking or concurrency control for apply versus edits. Last write wins, and every read recalculates, so a stale result fixes itself on the next read.
- A separate Risks section, acceptance metrics, and more alternatives.

## Given to the approver

The coordinator sent a message while you were working:
The agent's message:

Stage 8 (Intermediate Zoom Out) is complete. Findings are recorded in [intermediate_zoom_out_report.md](~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/intermediate_zoom_out_report.md).

How would you like to proceed?

1. Proceed to Stage 9 (Implementation Readiness Test)
2. Update the document first, then rerun Stage 8
3. Pause the review

Address this before completing your current task.

- tool call `Read`: `{"file_path": "~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/intermediate_zoom_out_report.md"}`

## Approver's reply

Option 1: go on to Stage 9. Every finding here is a constraint I have already accepted and recorded, so the document needs no changes.

## Given to the approver

The coordinator sent a message while you were working:
The agent's message:

Stage 9 is complete. Findings are recorded in [implementation_readiness_report.md](~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/implementation_readiness_report.md).

How would you like to proceed?

1. Conclude review and finalize the document
2. Resolve findings with an agent
3. Update the document manually, then rerun Stage 9
4. Pause the review

Address this before completing your current task.

- tool call `Read`: `{"file_path": "~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/implementation_readiness_report.md"}`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/ea1/repo; grep -n -B2 \"Product product\" sm-core-model/src/main/java/com/salesmanager/core/model/shoppingcart/ShoppingCartItem.java; grep -rn \"setProduct(\" sm-core/src/main/java/com/salesmanager/core/business/services/shoppin`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/ea1/repo; grep -n -B3 \"Set<Category> categories\" sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/Product.java; grep -n \"ShoppingCartDataPopulator\" sm-shop/src/main/java/com/salesmanager/shop/store/con`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/ea1/repo; sed -n 105,116p sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/Product.java; grep -n \"Transactional\" sm-core/src/main/java/com/salesmanager/core/business/services/shoppingcart/ShoppingCartCal`

## Approver's reply

Option 3: update the document yourself, then rerun Stage 9. Here is my decision on each finding. Use one mechanism everywhere and remove every "if needed", "or" and "fallback".

1. **Binding errors.** Use controller-local `@ExceptionHandler` methods inside `DiscountCodeApi`. Spring checks these before any `@ControllerAdvice`, so they win over `RestErrorHandler`. Handle `HttpMessageNotReadableException` (malformed JSON, null or missing body, bad date or number) and `MethodArgumentTypeMismatchException` (non-numeric `{id}`). Both return 400 with the same error-body class and fields that `RestErrorHandler` already produces for its 400s. Name that class.

2. **Processor wiring.** Remove `PromoCodeCalculatorModule` from `ProcessorsConfiguration.orderTotalsPostProcessors()`, along with its field and import. Then delete the `PromoCodeCalculatorModule.java` class and `PromoCoupon.drl`. Mark these unchanged: `shopizer-core-ordertotal-processors.xml` (its registration is already commented out), `Constants`, `ManufacturerShippingCodeOrderTotalModuleImpl`, and every other `OrderTotalVariation` module.

3. **Product categories.** `ShoppingCartItem.product` is `@Transient`. `ShoppingCartServiceImpl.getPopulatedItem` sets it when the cart is loaded, but `Product.categories` is LAZY. Use one mandatory path: a store-qualified JPQL query on `DiscountCodeRepository`, for example `select p.id, c.id, c.lineage from Product p join p.categories c where p.id in :productIds and p.merchantStore.id = :storeId`. The evaluator calls it once per evaluation with the product ids of the filtered items. A product with no rows has no categories. An item whose product is null has already been removed by the availability filter. Drop the `ProductService` fallback.

4. **Pricing contract.** There is no new pricing logic. `preparePricedAvailableItems(ShoppingCart)` returns `cart.getLineItems()` filtered to `product != null && product.isAvailable()`, exactly as `caculateShoppingCart` filters today. The `itemPrice` on each item is whatever `ShoppingCartServiceImpl` already set when it loaded the cart. A line subtotal is `pricingService.calculatePriceQuantity(itemPrice, quantity)`, the same call the mapper and `caculateOrder` use. Pull that line-subtotal computation into one helper that both `caculateOrder` and the evaluator call. The method makes no changes to the items.

5. **Single evaluation.** This is final: `caculateOrder` evaluates inside itself, based on `OrderSummary.getPromoCode()`, with no new parameter. `caculateShoppingCart` sets the summary's promo code from the cart. Remove any wording about passing a result into `caculateOrder`.

6. **Transactions.** `DiscountCalculationServiceImpl.evaluate` is `@Transactional(readOnly = true)` and returns before anything is saved. The cleared code is persisted through `shoppingCartService.saveOrUpdate(cart)`, which is the existing transactional service method, called from `OrderServiceImpl.caculateShoppingCart` after `caculateOrder` returns. Do not call the save from inside the read-only evaluator.

7. **Populators.**
   - `ReadableOrderTotalPopulator`: also recognize the `"discount"` code as a discount line, the same change as in `ReadableOrderTotalMapper`.
   - `ShoppingCartDataPopulator`: leave it unchanged. It is the legacy, non-v1 path, and it gets totals from the same calculation, so it picks up the line automatically. List it as unchanged and give that reason.

8. **Handling fees.** `total = subTotal − discount + shipping + handling + tax`. The discount is ≥ 0 and capped at the post-variation `subTotal`, so the total is never negative.

9. **Category edge cases.**
   - No categories configured (null or empty): every filtered item is eligible, including products with no categories.
   - Categories configured, but none of the category codes resolves: no item is eligible, so the code does not apply.
   - Categories configured and at least one resolves: products with no categories are not eligible.
   - In every case the minimum is checked against the whole filtered cart subtotal.

10. **Entity mapping.**
    - `@ManyToOne(fetch = LAZY, optional = false) @JoinColumn(name="MERCHANT_ID", nullable=false)`, with no cascade.
    - The id generator copies the convention used by the existing entities, for example the `@TableGenerator`/`SM_SEQUENCER` pattern. Cite the entity you copy from.
    - The `@ElementCollection` table gets `DISCOUNT_CODE_ID` as its FK, and Hibernate deletes its rows when the `DiscountCode` is deleted or the set is replaced.
    - Columns: `CODE`/`CODE_NORMALIZED` VARCHAR(100), and VALUE/MINIMUM_SUBTOTAL DECIMAL(19,4).

11. **Store and authorization.** `?store=` behaviour is whatever `MerchantStoreArgumentResolver` does today: it defaults to DEFAULT when the parameter is absent, and an unknown store gives `ResourceNotFoundException`, which is a 404. Do not add anything. Every one of the four CRUD methods calls `authorizationUtils.authenticatedUser()` and then `authorizationUtils.authorizeUser(...)`.

12. **Checkout.** In `OrderFacadeImpl`, in the block that today checks `promoAdded` (inside the method that builds the order total summary from the cart; name the method), remove the expiry check and set `summary.setPromoCode(shoppingCart.getPromoCode())` whenever it is not blank. `caculateOrder` then re-evaluates it. If the code no longer applies, the totals have no discount line, so the order gets no discount. The cart itself is cleared on its next read through `caculateShoppingCart`, and checkout needs no extra persistence.

13. **Category-code case.** Category codes are stored and matched exactly as given, through `CategoryService.getByCode(store, code)`. Duplicates collapse only when they are exactly equal.

14. **Verification.** Name an explicit command, for example `./mvnw -pl sm-shop -am test -Dtest='DiscountCode*Test,ShoppingCartDiscount*Test' -DfailIfNoTests=false` plus the core unit tests. Add one test that, after context startup, saving two codes that differ only in case in the same store fails at the database. Running the integration tests covers the element-collection table.

15. **Nits.** Remove the remaining alternatives from the detailed sections and split up the dense paragraphs.

## Given to the approver

The coordinator sent a message while you were working:
The agent's message:

Stage 9 rerun is complete. Findings are recorded in [implementation_readiness_report.md](~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/implementation_readiness_report.md).

How would you like to proceed?

1. Conclude review and finalize the document
2. Resolve findings with an agent
3. Update the document manually, then rerun Stage 9
4. Pause the review

Address this before completing your current task.

- tool call `Read`: `{"file_path": "~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/implementation_readiness_report.md"}`

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/ea1/repo; grep -n -A3 \"TableGenerator\" sm-core-model/src/main/java/com/salesmanager/core/model/catalog/category/Category.java; grep -n \"private\\|public ErrorEntity\" sm-shop/src/main/java/com/salesmanager/shop/store/api/exce`

## Approver's reply

Make these edits yourself, then go straight to option 1, Conclude and finalize. No further Stage 9 rerun is needed.

1. **Category query projection.** Add an interface projection `ProductCategoryRow { Long getProductId(); Long getCategoryId(); String getLineage(); }` and this query: `@Query("select p.id as productId, c.id as categoryId, c.lineage as lineage from Product p join p.categories c where p.id in :productIds and p.merchantStore.id = :storeId") List<ProductCategoryRow> findProductCategoryRowsByStoreAndProductIds(@Param("storeId") Integer storeId, @Param("productIds") Collection<Long> productIds)`. Before running it, check the real type of the `MerchantStore` id and use that. The evaluator groups the rows into a `Map<Long productId, List<ProductCategoryRow>>`. A product id with no entry has no categories. Duplicate rows are harmless, because eligibility is an any-match. Skip the query entirely when the list of ids is empty.

2. **Private `modifyCart(ShoppingCart, PersistableShoppingCartItem, ...)` in `ShoppingCartFacadeImpl`.** Remove the promo-code and `promoAdded` assignments there as well. Add a regression test: adding or modifying an item whose JSON includes `promoCode` leaves the cart's `promoCode` unchanged.

3. **List ordering.** Use `List<DiscountCode> findByMerchantStoreOrderByIdAsc(MerchantStore store)`.

4. **Id generator.** Copy `Category` exactly: `@TableGenerator(name = "TABLE_GEN", table = "SM_SEQUENCER", pkColumnName = "SEQ_NAME", valueColumnName = "SEQ_COUNT", pkColumnValue = "DISCOUNT_CODE_SEQ_NEXT_VAL")` with `@GeneratedValue(strategy = GenerationType.TABLE, generator = "TABLE_GEN")`.

5. **Clamping.** `discount = min(computedDiscount, max(subTotal, 0))`, which is at least 0. `total = max(subTotal − discount + shipping + handling + tax, 0)`. Apart from that, legacy variations behave exactly as they do today.

6. **Line subtotals.** Define one prepared-item structure: `PricedCartItem { ShoppingCartItem item; BigDecimal lineSubtotal; }`. Only `OrderService.preparePricedAvailableItems(ShoppingCart)` creates it, computing `lineSubtotal` with `pricingService.calculatePriceQuantity(item.getItemPrice(), item.getQuantity())`. `caculateOrder` builds the list through that same method from `summary.getProducts()` (or an overload that takes the item list), and the apply path calls the same method. The evaluator takes `List<PricedCartItem>` and never computes prices itself.

7. **Error body.** `ErrorEntity` has `errorCode` and `message`. The controller-local handlers return HTTP 400 with `errorCode = "400"` and `message = exception.getMessage()`. Before writing this, check how `RestErrorHandler` fills `errorCode` for its existing 400s and match that.

8. **Read path.** The mapper's single `shoppingCartCalculationService.calculate` call is the only calculation on the read path. `getByCode` does no calculation of its own. Fix the overview to say this.

9. **Nits.**
   - Fix the duplicated "controller-local".
   - Remove the optional `Clock` sentence; the rule is plain `LocalDate.now()`.
   - Remove the volume-justification and acceptance-metrics prose.

Once that is done, finalize the document.

## Given to the approver

The coordinator sent a message while you were working:
The agent's message:

The requested edits are applied, and the design is finalized in [design_draft.md](~/code/benchmark/skills-impact-work/egm-runs/ea1/repo/design_draft.md).

Address this before completing your current task.

- tool call `Bash`: `{"command": "cd ~/code/benchmark/skills-impact-work/egm-runs/ea1/repo; grep -n \"ProductCategoryRow\\|findByMerchantStoreOrderByIdAsc\\|DISCOUNT_CODE_SEQ_NEXT_VAL\\|PricedCartItem\\|max(subTotal\\|controller-local controller-local\\|Clock\\|errorCode\\|promoCode. unchanged\\|minimum.*whol`

## Approver's reply

APPROVED FOR BUILD
