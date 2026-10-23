# Stage 5 — Initial Zoom Out Review (Rerun 2)

Target: `design_draft.md` (full document; FeatureRange 1–324, DetailedRange 325–561)
Reviewer: `egm-zoom-out` (Skeptical Architect)

The dependency direction and legacy-variation ordering are now explicit: price
preparation is on `OrderService`, and the merchant discount is applied after
existing variations with a defined total invariant.

## Findings

### Major — No-code cart recalculation path is undefined

**Affected scope:** `design_draft.md` lines 191–203 and 367–384.

The evaluator runs on every cart recalculation, but its specified implementation
normalizes `promo` immediately with `promo.toUpperCase(Locale.ROOT)` and does
not define null/blank handling. A cart without a saved promo could therefore
fail instead of returning `DiscountApplicationResult.notApplicable()`. Add an
explicit no-code path before normalization.

### Major — Rounded zero conflicts with the positive discount contract

**Affected scope:** `design_draft.md` lines 70–80, 214–220, and 512–537.

A valid percentage can round to `0.00` under one-time `HALF_UP` rounding (for
example, 1% of a $0.01 eligible subtotal). The plan does not say whether that
application is rejected or retained, so it could retain a promo code while
emitting no positive discount or emit a zero line. Define post-rounding-zero
behavior explicitly to preserve the response contract.
