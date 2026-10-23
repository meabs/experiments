# Stage 6 — Comprehension Test

## Findings

### Major — API contracts are not self-contained

**Affected scope:** Goals, Technical Plan, and Detailed Implementation Plan.

The draft names CRUD routes and status codes but omits complete method/path contracts, request and response fields, ID/path parameters, authentication mechanism, error-body shape, list/pagination behavior, and the existing cart promo endpoint path. A fresh implementer cannot reliably implement or consume the APIs from this document alone.

### Major — Discount semantics are incomplete

**Affected scope:** Technical Plan and discount model/service implementation list.

The document does not restate percentage limits, whether percentage discounts use eligible line-item totals, fixed-amount caps, zero-value rules, or the precise meaning of “value rules” and “amount caps.” These choices directly determine validation and totals.

### Major — Date behavior is underspecified

**Affected scope:** Technical Plan and verification plan.

“Inclusive dates” does not define date/time representation, timezone, omitted-bound behavior, or exact boundary handling. The verification plan mentions boundaries without stating the contract.

### Major — Category and subtotal eligibility are unclear

**Affected scope:** Technical Plan and cart/order integration items.

“Including descendants” does not state whether the configured category itself qualifies, how multiple categories combine, how uncategorized products behave, or how category deletion/moves affect carts. Subtotal is also undefined with respect to shipping, tax, existing discounts, and excluded lines.

### Major — Invalid-code cleanup lifecycle is unstated

**Affected scope:** Technical Plan and cart mapping items.

The draft says cart reads clear an invalid code but does not define whether that write is transactional, how concurrent reads and code edits behave, or whether order creation recalculates independently.

### Nit — Project terms are undefined

**Affected scope:** Architecture and Alternatives sections.

Terms such as `MerchantStore`, Drools, DTO, private API, aggregate, readable-cart mapping, and half-up rounding are not defined or linked. A short glossary or inline definitions would help fresh readers.

## Stage Result

The document’s intent is understandable, but the API and discount-rule contracts need explicit definitions before implementation can proceed safely.

