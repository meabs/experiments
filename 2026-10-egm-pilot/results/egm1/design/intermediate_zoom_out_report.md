# Stage 8 — Intermediate Zoom Out Review

*Target:* [design_draft.md](~/code/benchmark/skills-impact-work/egm-runs/egm1/repo/design_draft.md)

## Findings

### Major — Persistence and migration strategy contradict each other

**Affected scope:** Decisions, implementation item 3, Compatibility.

The document commits to Hibernate schema update with no migration framework but
also instructs creation of migration resources, tables, indexes, and foreign
keys. Choose one existing schema mechanism and specify only its required change.

### Major — Keep one owner for discount monetary calculation

**Affected scope:** Data/service layer, cart presentation, implementation item 2.

The eligibility service and `PromoCodeCalculatorModule` both appear to compute
discounts. Define the service as the eligibility/domain decision (or the sole
calculation owner) and keep one producer of the total line. Explicitly remove
the Drools `PromoCoupon.drl`/`DroolsBeanFactory` path.

### Major — Read-time invalidation is a write-heavy concurrency path

**Affected scope:** Cart presentation; read-time invalidation mitigation.

Every GET may recalculate, mutate, retry, and read again. Justify this
complexity with the consistency requirement and define one minimal transaction
boundary, or omit invalid codes at calculation time and persist clearing during
normal cart mutations.

### Major — Tax and total semantics still need an example

**Affected scope:** CUJ 2, cart presentation, money/compatibility requirements.

The document still does not establish existing `OrderTotal` sign conventions or
show before/after totals including tax and shipping. Add a concrete example that
proves the discount is applied once and clarifies the taxable basis.

### Major — Category persistence is still an open choice

**Affected scope:** Data/service layer; implementation item 1.

“A relation or validated join representation” is unresolved. Select the existing
category-association pattern and define behavior when categories are deleted.

### Major — Name the authorization boundary

**Affected scope:** Admin API; security and tenancy.

Identify the existing private controller/filter, required role, order of
authorization versus store/id lookup, and denied-store response.

### Nit — Performance indexes are premature

**Affected scope:** Performance requirements and data layer.

The index and query-count requirements lack a measured bottleneck. Start with
existing repository access patterns and add indexes only when the chosen schema
and measurements justify them.

### Nit — Make the clock injectable

**Affected scope:** Decisions and eligibility service.

Name a deterministic clock source for date-boundary tests instead of relying on
system time.

## Checkpoint

Stage 8 is complete. The next stage must not begin until these findings are
accepted or revision instructions are provided.
