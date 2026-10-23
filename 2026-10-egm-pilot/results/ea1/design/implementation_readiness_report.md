# Stage 9 — Implementation Readiness Test (Rerun)

Target: `design_draft.md`, Detailed Implementation Plan

Reviewers: `egm-implementation-readiness`, `egm-codebase-details`, `egm-style`

## Findings

### Major — Category projection query needs an exact contract

`DiscountCodeRepository.findProductCategoryRowsByStoreAndProductIds` is named,
but the document does not define its projection type, exact JPQL joins and
selected fields, product/store predicates, duplicate-row behavior, or mapping
back to each `ShoppingCartItem`. Specify a concrete projection record/class and
the representation for product IDs with no category rows.

### Major — One cart mutation path still sets promo state

`ShoppingCartFacadeImpl`'s private `modifyCart(ShoppingCart,
PersistableShoppingCartItem, ...)` currently copies the item's promo code and
sets `promoAdded`. The plan names `updateCartItems`, `addToCart`, and
`readableShoppingCart`, but not this setter. Explicitly ignore/remove this
assignment and add regression coverage so the validated promo endpoint is the
sole cart-code setter.

### Major — Admin list ordering is not enforced

The API promises ID-ascending results, but `findByStore` has no ordering
contract. Specify an explicit repository query such as
`findByMerchantStoreOrderByIdAsc(MerchantStore store)` or a facade sort.

### Major — Sequence-generator configuration remains ambiguous

“Copy the `MerchantStore`/`SM_SEQUENCER` convention” does not specify the
generator name or `pkColumnValue` for the new entity. State the exact
`@TableGenerator` configuration and its `DISCOUNT_CODE_ID` key so it cannot
collide with another entity.

### Major — Negative subtotal and final-total clamping are undefined

The design caps the discount at `summary.subTotal` and requires non-negative
discount and total, but does not define behavior when a legacy variation makes
`subTotal` negative or when shipping, handling, and tax produce a negative
result. Specify the exact clamp/order-of-operations that preserves the
invariants.

### Major — Line-subtotal ownership remains ambiguous

The evaluator receives already-computed subtotals, while the shared helper is
described as computing them in `caculateOrder`, and the apply path invokes the
evaluator directly. State the exact prepared-item structure and the single
point at which line subtotals are populated for both paths.

### Major — Error-body details are still indirect

The document now names `ErrorEntity`, but does not list its fields or the exact
400 status/message mapping used by the controller-local handlers. State the
fields and mapping explicitly.

### Major — Recalculation wording still implies duplicate work

The overview mentions recalculation in both `getByCode` and the mapper, while
the detailed plan says `getByCode` relies on the mapper. State that the mapper's
single `shoppingCartCalculationService.calculate` call is the read-path
calculation and `getByCode` performs no independent calculation.

### Nit — Remove duplicated wording

Item 14 says “controller-local controller-local `@ExceptionHandler`”.

### Nit — Remove optional clock language and meta-scope prose

The optional test `Clock` bean remains an implementer choice despite the
zero-decision rule. The volume justification and the “no separate
acceptance-metrics program” sentence are also non-actionable prose.

