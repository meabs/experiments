# Stage 7 — Critic Review

*Target:* [design_draft.md](~/code/benchmark/skills-impact-work/egm-runs/egm1/repo/design_draft.md)

## Findings

### Blocker — Approved status conflicts with unresolved architecture

**Affected scope:** Open Questions, Technical Plan, Detailed Implementation Plan.

The document is marked `Approved` while persistence ownership, migration
mechanism, cart response compatibility, category queries, and authorization
implementation remain open. An implementation team would need to make design
choices independently. Resolve these questions and identify concrete modules,
DTO/status behavior, authorization, and category repository queries before the
document can serve as an implementation specification.

### Major — Reuse the existing pricing pipeline explicitly

The design must identify how the merchant-record lookup replaces the current
rules-backed promo calculation, how discount totals enter the existing order
pipeline, and how checkout avoids duplicate discounts. Name the existing pricing
components and the single calculation seam.

### Major — Complete validation and API contracts

The document omits an explicit validation matrix, normalization rules, precision
and scale, minimum-subtotal constraints, category lifecycle behavior, and
currency handling. It also lacks concrete request/response schemas, PUT
replacement semantics, list pagination, not-found and malformed-id behavior, and
authorization error responses. Add an endpoint table with representative JSON.

### Major — Resolve eligibility and date semantics

Specify whether the minimum subtotal is measured over the whole cart or eligible
items, the exact price/tax/quantity basis, the business timezone and date source,
and how category hierarchy edits affect existing codes. Include boundary tests.

### Major — Define cart persistence and concurrency

Recalculation that clears a code during a read is a write with race conditions.
Define whether the cart stores a code string, discount id, or snapshot; rename
and delete behavior; idempotent invalidation; transaction/locking/versioning;
and concurrent apply/edit/delete outcomes.

### Major — Define total-line and tax/shipping behavior

`subtotal - discount` is insufficient against Shopizer’s tax, shipping, and
existing total-line conventions. Specify processor ordering, sign handling,
taxable basis, currency scale, and examples that prevent double subtraction or
negative totals.

### Major — Make persistence and migration portable

The proposed uniqueness index and migration location are not tied to the
project’s actual supported database setup. Define schema evolution, legacy data,
rollback, concurrent constraint handling, and 409 mapping.

### Major — Expand alternatives and risk structure

Evaluate viable choices such as discount id versus code snapshot, apply-time
versus read-time calculation, and materialized versus recursive category
membership. Add a dedicated Risks & Mitigations section with failure modes,
limits, and mitigations.

### Major — Define concrete terms and measurable constraints

Explain `MerchantStore` resolution, validated join representation, category
descendants, readable-cart mapper, and cart-returning endpoints. Replace vague
performance phrases such as “bounded category data” with query/count bounds and
latency or error targets.

### Nit — Structural and style cleanup

Rename “The Problem” to “Problem Statement,” add requirement-to-CUJ-to-test
traceability, standardize Markdown list formatting, remove repeated overview
wording, and avoid process-oriented phrases such as “requested operating model.”

### Nit — Rounding example and legacy targets

Make the half-up test reproducible with exact inputs and explicitly name the
legacy Drools rule/module/configuration and fixtures that must be removed or
bypassed.

## Checkpoint

Stage 7 is complete. The next stage must not begin until these findings are
accepted or revision instructions are provided.
