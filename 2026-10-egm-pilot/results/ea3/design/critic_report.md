# Stage 7 — Design Critique

## Real defects requiring a design decision

### Major — Code length validation is missing

**Affected scope:** Entity/API validation and implementation list (lines 73, 150–169).

The entity limits codes to length 100, but the API contract does not validate that limit before persistence. Oversized input could become a database error instead of the documented 400 response.

**Proposed resolution:** Add a maximum length of 100 after trimming to the 400 validation rules and DTO/service tests.

### Major — Lazy category data loading is unspecified

**Affected scope:** Category matching (lines 114–118).

Evaluation depends on Product.getCategories() and Category.lineage, but the design does not state how these lazy associations are loaded during cart/order evaluation. The implementation could trigger N+1 queries or fail after entities detach.

**Proposed resolution:** State that evaluation runs inside the existing order/cart transaction and that the product/category query used for available cart items fetches Product.getCategories() and the needed Category fields before DiscountService.evaluate. Add an integration test using persisted entities loaded through the normal repository path.

### Major — Shared evaluation result propagation needs one explicit contract

**Affected scope:** Technical flow and mutation paths (lines 95–108, 120–126, 171).

The design has one DiscountService.evaluate contract, but cart mutation paths call it before the later caculateOrder pass. The document does not explicitly state that both use the same post-change available-item list, subtotal helper, store, and category loading, or how a failed non-throwing evaluation leaves the prior code.

**Proposed resolution:** State that all mutation paths call the same evaluate(store, code, availableItems, subtotal) contract after applying the change in memory, using the shared OrderService subtotal helper and cart store. On failure, only modifyCart throws; updateCartItems and add-item paths restore the prior promoCode and save the cart without raising. The subsequent cart response runs the same evaluate contract in caculateOrder.

## Findings rejected as out of scope or already addressed

### Major — Schema migration and rollout

**Affected scope:** Entity/schema plan (lines 67–84, 200–220).

The reviewer requested a migration mechanism, DDL, rollout, and rollback strategy. This project uses Hibernate hbm2ddl.auto=update, and migrations/rollout mechanics are outside this feature request.

**Proposed resolution:** No design change. Keep explicit entity annotations and state migrations and rollout/backfill as Non-Goals.

### Major — Test1234 rule removal

**Affected scope:** Legacy-rule goal and implementation list (lines 27, 108, 215–216).

The reviewer reported that rule removal was missing, but the current design already deletes PromoCoupon.drl, unregisters and deletes PromoCodeCalculatorModule, and requires a Test1234 regression test.

**Proposed resolution:** No change; retain the existing explicit deletion and regression test.

### Nit — Pagination and ordering for code lists

**Affected scope:** GET list endpoint.

Pagination and bounded list behavior are not requested. Adding them would expand the feature.

**Proposed resolution:** Treat pagination, ordering guarantees, and dataset limits as Non-Goals; leave GET behavior as the store's code list.

### Nit — Canonical heading names

**Affected scope:** Overview headings.

The content is present and the hierarchy is valid; renaming headings would improve template matching but would not change behavior.

**Proposed resolution:** Preference only; no functional change required.

## Style and structural cleanup

### Major — Repeated totals/evaluation contract

**Affected scope:** Technical plan and arithmetic sections (lines 104–126).

The same rules appear in several dense paragraphs, which can drift.

**Proposed resolution:** Consolidate the authoritative evaluate contract and totals JSON contract into one subsection, then make the flow and implementation list reference that subsection.

### Major — Total and promoCode wording consistency

**Affected scope:** CUJs, totals, compatibility, and response contract.

Some text says the total is subtotal minus discount, while other text includes shipping/handling/tax; older CUJ wording says “empty” while the explicit contract says null.

**Proposed resolution:** Use one wording everywhere: subtotal is undiscounted; the discount line reduces the item subtotal; existing shipping, handling, and tax are then added; final total is subtotal minus discount plus those existing amounts; no-code promoCode is null.

### Major — Authorization instruction is not self-contained

**Affected scope:** Private API contract (line 130).

“Copy that API’s existing admin/store authorization boundary exactly” requires a builder to reverse-engineer another API.

**Proposed resolution:** Keep TaxClassApi as the concrete template and add the observable rule: unauthenticated requests are 401, authenticated users without permission for the resolved store are 403, and authorized store administrators may access only that store's codes.

### Major — “Every add-item promo path” is vague

**Affected scope:** ShoppingCartFacadeImpl plan (line 171).

The affected mutation call sites are not named precisely enough to verify coverage.

**Proposed resolution:** Enumerate the existing updateCartItems path and both current item.getPromoCode() call sites, including the secondary path around line 933, and require all three to use the shared evaluation contract.

### Nit — Legacy one-day wording

**Affected scope:** Overview/problem statement.

“Valid for one day after it is added” is less precise than the later UTC-date policy.

**Proposed resolution:** Say the legacy one-day cart expiry is removed and eligibility is determined only by the code's UTC start/end dates.

### Nit — Test1234 wording

**Affected scope:** Non-Goals.

The string is not an inactive persisted entity.

**Proposed resolution:** Say the built-in rule is removed and the string has no effect unless a merchant creates it.

### Nit — Status wording

**Affected scope:** CUJ 2.

“The response is successful” is less precise than the endpoint contract.

**Proposed resolution:** State that a successful promo application returns 201 Created.

### Nit — Colloquial constraint wording

**Affected scope:** Entity uniqueness discussion.

“Rather than leaking a database constraint exception” is informal.

**Proposed resolution:** Replace with “map database constraint violations to 409 Conflict.”

### Nit — Broad exception wording

**Affected scope:** Error mapping.

“Wrapped constraint violations” and “malformed JSON generally” are broad.

**Proposed resolution:** Name DataIntegrityViolationException and nested constraint violations for conflict mapping; map HttpMessageNotReadableException for Jackson enum/date/JSON parse failures to 400.

## Checkpoint

Stage 7 is complete. Proposed resolutions are listed without applying edits.
