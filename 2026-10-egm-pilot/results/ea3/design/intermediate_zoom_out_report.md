# Stage 8 — Intermediate Zoom-Out Review

## Real defects requiring a design decision

### Major — Direct cart reads bypass recalculation

**Affected scope:** Technical flow, cart facade/mapper files, and CUJ 3.

The design says every cart response recalculates and clears deactivated, deleted, expired, or ineligible codes. Current ShoppingCartFacadeImpl getByCode and getById paths call ReadableShoppingCartMapper directly, while the mapper is explicitly read-only. Those responses can therefore return stale promoCode and totals.

**Proposed resolution:** Route every cart-read entry point, including getByCode and getById, through OrderServiceImpl.caculateShoppingCart before mapping. Keep the mapper read-only. Name those methods in the implementation plan and add integration assertions for GET responses after item removal, deactivation, and deletion.

### Major — Successful evaluation must return the stored spelling

**Affected scope:** Shared evaluate contract and apply flow.

DiscountService.evaluate currently returns only Optional<BigDecimal>, but a successful shopper application must persist the merchant’s original stored spelling. The design does not define how the caller obtains that spelling without another lookup.

**Proposed resolution:** Return a small evaluation result containing the rounded discount and the canonical stored code, with an empty result for ineligible codes. Use that result in modifyCart and the other mutation paths; do not perform a second lookup.

### Major — Atomic clearing boundary is not established

**Affected scope:** Consistency requirement and caculateShoppingCart.

The design requires recalculation and code clearing to be transactional, but only DiscountServiceImpl.evaluate is explicitly transactional. The surrounding cart clear/save and response operation is in OrderServiceImpl and has no stated transaction boundary.

**Proposed resolution:** Put the transaction boundary on the OrderServiceImpl cart calculation operation that evaluates, clears/saves, and builds the totals, while retaining the service transaction for direct mutation evaluation. State that the cart read returns only after the clear/save commits.

### Major — Batch-loading requirement conflicts with the chosen reuse path

**Affected scope:** Performance requirement and category evaluation.

The document asks for batch-loaded product categories but also says to use the normal product-service repository path with no custom fetch query. A transaction prevents detachment but can still cause one query per product.

**Proposed resolution:** Remove the batch-loading requirement from Non-Functional Requirements. Keep the requested transaction and normal repository path; do not add a fetch query unless an integration test demonstrates a lazy-loading failure. Query optimization is outside this feature.

## Preference / simplification

### Nit — Reuse the existing category lookup

**Affected scope:** CategoryService implementation item and architecture flow.

The codebase already exposes store-scoped CategoryService.getByCode(MerchantStore, String), backed by CategoryRepository.findByCode. Modifying CategoryService solely to add another resolution API risks duplicate behavior.

**Proposed resolution:** Reuse the existing getByCode method and remove the CategoryService/CategoryServiceImpl modification from the file list unless implementation discovers a concrete missing behavior.

## Checkpoint

Stage 8 is complete. Proposed resolutions are listed without applying edits.
