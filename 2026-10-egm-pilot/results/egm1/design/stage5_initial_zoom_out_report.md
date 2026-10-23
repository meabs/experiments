# Stage 5 — Initial Zoom Out Review

*Target:* [design_draft.md](~/code/benchmark/skills-impact-work/egm-runs/egm1/repo/design_draft.md)

## Findings

### Major — Reuse the existing pricing pipeline

**Affected scope:** Technical Plan → Data and service layer / Cart application
and presentation; Detailed Implementation Plan items 2 and 5.

The design proposes a new discount eligibility/calculation service and a new
cart-read recalculation path, but the codebase already has
`PromoCodeCalculatorModule`, `ShoppingCartCalculationService`,
`OrderService.calculateShoppingCartTotal`, `ReadableShoppingCartMapper`, and the
shared `OrderTotal`/`ReadableOrderTotal` pipeline. `PromoCodeCalculatorModule`
already evaluates promo codes and emits discount totals. Replacing its
rules-backed calculation with merchant-record lookup, then routing through the
existing calculation pipeline, avoids a parallel pricing path and reduces
inconsistent totals across cart and order APIs.

The design should explicitly reuse or extend these components rather than
introduce a second calculation architecture.

### Nit — Reuse existing category hierarchy infrastructure

**Affected scope:** Open Questions → category descendants; Technical Plan →
eligibility service step 3.

Code search found existing hierarchy infrastructure:
`CategoryService.getListByLineage(...)`, `CategoryRepository.findByLineage(...)`,
and lineage maintenance in `CategoryServiceImpl.addChild`. The design should
resolve descendants through this established service/repository instead of
leaving it as an open question or implying a new descendant-query mechanism.
This avoids duplicate hierarchy logic and loading the full catalog.

### Major — Consolidate existing cart paths at one calculation seam

**Affected scope:** Technical Plan → Cart application and presentation;
Compatibility and Consistency requirements.

The design says “all cart-returning endpoints” will use one centralized path,
but current code has multiple paths: `ShoppingCartFacadeImpl.getByCode`,
`ReadableShoppingCartMapper`, `ShoppingCartCalculationService`, and separate
promo-validity logic in `OrderFacadeImpl`. Without explicitly consolidating or
delegating these paths, stale or contradictory totals can remain.

The architectural fix should identify the existing calculation/mapper seam as
the single source of truth and remove legacy date-based checks, rather than
layering another recalculation step on top.

## Checkpoint

Stage 5 is complete. The next stage must not begin until these findings are
accepted or the requested revisions are specified.
