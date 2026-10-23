# Stage 9 — Implementation Readiness Test

## Real defects requiring a design decision

### Major — The injected UTC Clock has no production wiring

**Affected scope:** DiscountServiceImpl and verification plan.

The plan requires an injectable Clock but lists no Spring bean or configuration change. The codebase has no existing Clock bean, so constructor/field injection would fail unless the plan defines one.

**Proposed resolution:** Add a named Clock bean in the existing core Spring configuration that returns Clock.systemUTC(). Inject it into DiscountServiceImpl. In unit tests construct the service with a fixed Clock; do not add a production test configuration.

### Major — Checkout store propagation is incomplete

**Affected scope:** OrderServiceImpl.caculateOrder, OrderFacadeImpl, and OrderSummary.

OrderSummary has no store field, while caculateOrder receives the facade-supplied MerchantStore. The plan removes the facade's one-day check but does not state how the cart's own store reaches checkout evaluation. A request/store mismatch could evaluate the code against the wrong merchant.

**Proposed resolution:** In OrderFacadeImpl, pass the cart's own shoppingCart.getMerchantStore() as the MerchantStore argument to orderService.caculateOrderTotal for cart checkout. Keep the shopper code on OrderSummary; do not add a store field to OrderSummary.

### Major — Canonical code spelling is not propagated on recalculation

**Affected scope:** DiscountEvaluation, OrderServiceImpl, ReadableShoppingCartMapper.

DiscountEvaluation contains the canonical stored code, but the design does not say how the mapper receives it. The mapper currently reads source.promoCode before calculation, so an admin spelling edit can leave an old cart spelling in the response.

**Proposed resolution:** Have the authoritative cart calculation set ShoppingCart.promoCode to DiscountEvaluation.canonicalCode before totals are mapped, and persist that update in the same transaction. The mapper calls calculate first, then reads the updated source.promoCode; when no discount total exists it sets the response promoCode to null.

### Major — Cart promo not-found handling is unspecified

**Affected scope:** ShoppingCartFacadeImpl.modifyCart(String, String, ...).

The current method can dereference a null cart before the documented 404 mapping. “Load the cart” is not enough to make the implementation safe.

**Proposed resolution:** Require an explicit null result check immediately after shoppingCartService.getByCode; return the existing not-found result so ShoppingCartApi maps it to 404 before evaluating the candidate.

### Major — File-level plan is not zero-decision actionable

**Affected scope:** Items 1–26.

Several entries say “fields above,” “duplicate checks,” or “typed exceptions” without exact public method signatures, repository predicates/return types, JPA relationship ownership/cascade/fetch, DTO validation annotations, list/delete response types, or API parameter/status annotations.

**Proposed resolution:** Add a compact contract table before the file list. Specify Discount fields and annotations; repository methods and return types; DiscountService CRUD/evaluate signatures; DiscountApi method signatures and response statuses; DTO field types/validation/defaults; and mapper direction. Keep algorithm details in the authoritative evaluation subsection.

### Major — Shared subtotal helper is not fully specified

**Affected scope:** OrderService and ShoppingCartFacadeImpl items.

The helper has no method name, signature, extraction point, or exact ordering contract.

**Proposed resolution:** Name it BigDecimal calculateCartSubtotal(List<ShoppingCartItem> items) on OrderService, extracted from the existing caculateOrder subtotal loop. It adds each base itemPrice × quantity and each one-time additional price exactly as the current loop does, before variations are subtracted. Require caculateShoppingCart, modifyCart, updateCartItems, and both item.getPromoCode paths to call it.

### Major — Mutation transaction and rollback behavior is incomplete

**Affected scope:** ShoppingCartFacadeImpl mutation items and consistency requirements.

Applying an in-memory item change, evaluating, saving, and mapping can fail after partial state changes. The plan does not define transaction boundaries or restoration when evaluation/save/response calculation fails.

**Proposed resolution:** Mark the three mutation operations transactional. Evaluate before the first save; on a failed candidate restore the prior promoCode and save only the item change for non-throwing paths; on modifyCart throw before saving any mutation. A successful path saves once after setting the canonical code. Runtime failures roll back the transaction.

### Major — Concurrent conflict handling is not actionable enough

**Affected scope:** DiscountServiceImpl save/update.

“Catch DataIntegrityViolationException and wrapped constraint violations” does not say how rollback or constraint identification works.

**Proposed resolution:** Make each create/update transaction rollback-only on DataIntegrityViolationException, inspect the cause chain for the DISCOUNT unique constraint, and translate only that violation to DiscountConflictException; rethrow unrelated integrity failures for the existing 500 handler.

### Major — No implementation phases or stable checkpoints

**Affected scope:** Detailed Implementation Plan.

The readiness standard requires incremental phases that leave the build testable, but the plan is a flat file list.

**Proposed resolution:** Add ordered phases: (1) entity/DTO and Hibernate update, (2) repository/service/evaluation and unit tests, (3) order/cart integration and cart integration tests, (4) private API/error mapping and API integration tests, (5) remove legacy rule and run full verification. Each phase must compile and run its listed tests before the next begins.

### Major — DTO/API contracts remain partially implicit

**Affected scope:** PersistableDiscount, DiscountApi, DiscountFacade, RestErrorHandler.

The plan does not give exact DTO validation annotations, list/delete response types, facade method signatures, or endpoint parameter annotations.

**Proposed resolution:** Add the contract table described above: one PersistableDiscount with code String max 100 and not-blank, type DiscountType not-null, value BigDecimal not-null positive, optional minimumSubtotal BigDecimal non-negative, ISO LocalDate dates, categories List<String>, active Boolean default true; list returns List<PersistableDiscount>; delete returns void/200; API methods receive MerchantStore and request DTO and use the stated statuses.

### Major — Existing cart mapper test reference is missing

**Affected scope:** Verification plan.

The plan names cart mapper tests in the command but no mapper test file appears in the current test inventory.

**Proposed resolution:** Add sm-shop/src/test/java/com/salesmanager/shop/mapper/cart/ReadableShoppingCartMapperTest.java to the test inventory, or remove the command reference. Prefer adding the exact file and assertions for calculate-before-promo and null-without-discount behavior.

## Preferences / clarifications

### Nit — Test schema fixture wording

**Affected scope:** Test setup and schema verification.

The repository has a static create_schema.sql fixture, while the design relies on hbm2ddl.auto=update. This is a test-environment clarification, not a production migration requirement.

**Proposed resolution:** State that integration tests use the existing test Spring context with hbm2ddl.auto=update so Hibernate creates the new tables and constraints; do not add migration files or production rollout work.

### Nit — Style compression in file list

**Affected scope:** Items 1–26.

Short labels such as “store/id lookup” and “typed exception propagation” reduce readability.

**Proposed resolution:** Expand them while adding the contract table.

## Checkpoint

Stage 9 is complete. Proposed resolutions are listed without applying edits.
