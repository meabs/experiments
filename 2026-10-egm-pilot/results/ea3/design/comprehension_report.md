# Stage 6 — Comprehension Test

## Real defects requiring a design decision

### Major — Deactivation behavior is not explicit

**Affected scope:** Eligibility rules, DiscountService.evaluate, and tests (lines 23, 80, 104–118, 153, 161).

The document lists active as an eligibility condition but never states in the evaluation contract that active=false returns Optional.empty(). A builder could apply a deactivated code.

**Proposed resolution:** Add active == false as the first eligibility rejection in DiscountService.evaluate; require the deactivation integration test to assert that the cart drops the code and discount on its next return.

### Major — PUT omission semantics are undefined

**Affected scope:** PUT contract and DTO (lines 142, 148, 216, 224).

PUT is described as replacing all mutable fields, but optional fields have no explicit omission behavior. Implementations could reset omitted fields or retain old values.

**Proposed resolution:** State that PUT is a full replacement: omitted active defaults to true, omitted startDate defaults to today, and omitted minimumSubtotal, endDate, and categories become null/empty (unrestricted). Require clients to send every desired field for retention.

### Major — Cart total and response representation are incomplete

**Affected scope:** CUJs, totals flow, compatibility notes (lines 57, 63, 106, 118, 188).

The draft says total is subtotal minus discount before shipping/tax, but does not state the final aggregation order or the response representation of totals. It also leaves promoCode as “empty/null according to the current DTO convention,” which requires undocumented code knowledge.

**Proposed resolution:** State that the existing order-total aggregation remains unchanged: the discount line reduces the undiscounted item subtotal, then existing shipping, handling, and tax lines are added in their current order. Specify the JSON contract as promoCode: "" when no code applies, one totals entry with code:"discount" and positive value when applicable, no discount entry otherwise, and total = subtotal - discount + existing shipping/handling/tax amounts.

### Major — Rounded zero discount is unspecified

**Affected scope:** Arithmetic and verification plan (lines 104, 118, 236–247).

A valid percentage can round to 0.00, conflicting with the statement that the returned discount is positive. The builder does not know whether to reject, clear, or emit zero.

**Proposed resolution:** Treat a rounded 0.00 result as not applicable: evaluate returns Optional.empty(), shopper apply receives 400, and an already-applied code is cleared on cart return.

### Major — Store query identity and authorization boundary are undefined

**Affected scope:** CUJ examples and private API contract (lines 49–51, 122, 146–156).

The store query parameter has no defined type or resolution behavior, and the draft refers to existing authentication and authorization without stating the boundary. A fresh implementer cannot know whether it is a store code, id, or slug.

**Proposed resolution:** State that ?store is the merchant store code (String), resolved by the existing MerchantStoreService.getByCode, and that the existing private endpoint security/filter rejects unauthenticated users or users not authorized for that store with the project’s standard 401/403 responses. Shopper discount evaluation always uses the cart’s MerchantStore object.

### Major — Concurrent uniqueness failures can become 500

**Affected scope:** Persistence uniqueness and error mapping (lines 82, 154, 157, 237, 246).

The design pre-checks duplicates and declares a database unique constraint, but does not map a constraint violation from a concurrent write to 409.

**Proposed resolution:** Catch the repository transaction’s unique-constraint/data-integrity exception in the discount write service, roll back the failed write, and throw DiscountConflictException so both pre-check and race paths return 409.

### Major — Category matching inputs are underspecified

**Affected scope:** Category matching and implementation inventory (lines 114, 118, 203–204).

The design compares lineage tokens to category IDs but does not define ID-to-string conversion, category-code case handling, null-lineage behavior, or the authoritative product-category collection.

**Proposed resolution:** Specify decimal Category.id.toString() tokens; category codes are matched case-sensitively as stored; a null/blank lineage matches no configured category; and the authoritative collection is Product.getCategories(), filtered to categories whose merchantStore.id equals the cart store id. Category-code resolution remains store-scoped and rejects unknown codes.

### Major — Existing item and subtotal behavior is not restated

**Affected scope:** Shared evaluation contract and file plan (lines 104, 118, 207–208, 225).

The contract depends on availableItems, itemPrice, quantity, one-time additional prices, and the subtotal helper without defining their observable behavior. A builder must inspect existing code to know what the contract means.

**Proposed resolution:** Define availableItems as the cart line items whose product has available=true; define each line base as stored itemPrice × quantity; define the subtotal helper as the exact existing caculateOrder subtotal including one-time additional prices before variations; and require all callers to pass those exact values to evaluate.

## Preferences / cleanup

### Nit — Whitespace normalization

**Affected scope:** Code normalization and validation (lines 73–75, 142, 161).

The draft lower-cases codes but does not say what happens to surrounding whitespace.

**Proposed resolution:** Trim leading/trailing whitespace before blank validation and normalization, store the trimmed merchant spelling, and compare trimmed lower-case values. This is a small clarity preference unless preserving whitespace is required by existing API behavior.

### Nit — File-list numbering

**Affected scope:** Detailed implementation list (lines 194–230).

The checklist skips item numbers 15 and 16, which can confuse tracking but does not change behavior.

**Proposed resolution:** Renumber the implementation list consecutively.

## Checkpoint

Stage 6 is complete. No document edits were applied; the proposed resolutions above are awaiting author direction.
