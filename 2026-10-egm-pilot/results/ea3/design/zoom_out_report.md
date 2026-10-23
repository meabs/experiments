# Stage 5 — Initial Zoom Out Review

## Findings

### Blocker — Exception module boundary

**Affected scope:** REST validation/error mapping and implementation files (design lines 158, 211–212, 228).

The plan places `DiscountConflictException` and `InvalidDiscountException` in `sm-core`, while requiring them to extend the runtime API exception base that exists in `sm-shop` (`sm-shop/src/main/java/com/salesmanager/shop/store/api/exception/*`). That creates an invalid core-to-shop dependency or requires duplicate exception hierarchies. The design must place domain exceptions in a shared/core-compatible layer and map them in the shop layer, or keep API exceptions entirely in `sm-shop`.

### Major — Non-cart order totals can omit discounts

**Affected scope:** Technical flow and `OrderServiceImpl` implementation (design lines 103–105, 207, 235–240).

The plan removes the existing post-processor and injects discounts only through the private `caculateOrder` path used by cart recalculation, while explicitly passing no discount to non-cart order-summary callers. Existing checkout/order-total flows call `caculateOrderTotal` directly and can therefore silently omit an applied merchant discount. The root requirement is cart/order pricing consistency; the design needs one shared discount calculation boundary or an explicit decision that discounts are cart-response-only with checkout consequences addressed.

### Major — Existing lineage query is not delimiter-safe

**Affected scope:** Category subtree matching and category repository/service files (design lines 111–113, 209–210).

The repository already has `CategoryService.getListByLineage` and `CategoryRepository.findByLineage`, but that query uses `c.lineage like %?2%`. Substring matching can include unrelated category ids (for example, root `2` matching lineage segments containing `12`), violating the claimed subtree and store-safety semantics. Reuse the existing lineage infrastructure only after defining a delimiter-safe descendant query; otherwise the new query is underspecified and risks incorrect discounts.

### Major — Subtotal definition can diverge from established pricing

**Affected scope:** Discount arithmetic and `OrderServiceImpl` (design lines 115–117, 207).

The plan says the discount service computes subtotal from `itemPrice × quantity`, but existing `OrderServiceImpl.caculateOrder` also adds one-time additional prices to `subTotal` and processes other price totals. Replacing that calculation with a parallel subtotal risks cart totals, minimum-subtotal checks, and displayed totals disagreeing with Shopizer’s established pricing model. The design must specify whether additional prices are included and reuse a single subtotal result rather than introducing a second arithmetic definition.

### Nit — Hibernate update rollout is not addressed

**Affected scope:** Schema statement and implementation plan (design lines 195–197, 231).

The draft relies on `hibernate.hbm2ddl.auto=update` to create a new entity and join table, while the repository convention uses explicit table-generator and schema naming patterns. No migration/rollout or existing-environment compatibility check is described, so deployments with existing databases may not receive the unique constraint or join table reliably.

### Nit — Mutation-path evaluation is underspecified

**Affected scope:** Cart mutation paths (design lines 225–226).

The plan asks several cart mutation paths to perform “non-throwing evaluation” and preserve the previous code, but does not define which item set, subtotal, or transaction boundary those evaluations use. This duplicates eligibility logic outside the single recalculation point and can produce temporary states that differ from the subsequent cart-read result. Centralize evaluation or specify a shared service contract for all mutation paths.

## Checkpoint

Stage 5 reviewed the full document against the Zoom Out Standard. The report is intentionally stopped here for author direction.
