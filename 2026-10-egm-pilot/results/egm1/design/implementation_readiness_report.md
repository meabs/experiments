# Stage 9 — Implementation Readiness Test

*Target:* [design_draft.md](~/code/benchmark/skills-impact-work/egm-runs/egm1/repo/design_draft.md)

## Result

The design is not implementation-ready under the zero-decision standard.

## Blockers

1. **Exact target files and symbols are missing.** Wildcards such as
   `discount/*`, `.../private...`, and “existing cart promo controller” leave the
   implementer to locate and choose classes. The plan must enumerate exact paths
   and symbols, including `PromoCodeCalculatorModule`, `OrderServiceImpl`,
   `ShoppingCartCalculationServiceImpl`, `ShoppingCartFacadeImpl`,
   `ReadableShoppingCartMapper`, `ShoppingCart`, `PromoCoupon.drl`, controller,
   DTO, repository, service, and test classes.

2. **Persistence and schema management are unresolved.** The design chooses
   Hibernate schema update but also requests migration resources. It must choose
   one mechanism and specify exact table/column names, entity mappings,
   join-table keys, nullability, cascade/delete behavior, indexes, and
   uniqueness handling. Category association cannot remain “relation or
   validated join representation.”

## Major Findings

3. **Cart state and concurrency are not actionable.** Define the exact
   `ShoppingCart` field, legacy `promoAdded` behavior, casing preservation,
   serialization/default handling, transaction boundary, version field (the
   current model has none), retry exception, and apply/read/edit/delete flows.

4. **The existing per-item pricing contract is not reconciled.** Current code
   uses Drools, `Double`, final product price, and item-level `OrderTotal`
   entries. The requested cart-level eligible-subtotal discount needs explicit
   changes to this contract and a rule preventing duplicate lines.

5. **Legacy behavior removal is incomplete.** One-day expiry and system-default
   timezone logic exist in multiple order, facade, and mapper paths. Name every
   edit and define the single owner of invalidation and response mapping.

6. **Promo application atomicity is unspecified.** `modifyCart` currently saves
   arbitrary promo strings. Name the eligibility exception, controller error
   mapping, transaction boundary, and exact preservation behavior on failure.

7. **Eligibility, money, timezone, and normalization still require choices.**
   Define exact subtotal/product-price fields, category source and overlap
   handling, timezone configuration and fallback, normalization algorithm and
   database representation, and separate precision rules for storage,
   comparison, discount output, and totals.

8. **Authorization and route composition are vague.** Identify the existing
   private controller annotation/filter, role, store resolver, class-level route,
   order of authorization versus id lookup, and JSON error bodies for invalid,
   unauthorized, cross-store, malformed-id, and constraint cases.

9. **Testing is thematic rather than executable.** Name test classes, fixtures,
   request payloads, expected bodies/statuses, database setup, and Maven module
   commands. Include all listed boundary, concurrency, invalidation, category,
   rounding, and cross-store cases.

10. **No implementation phases/checkpoints are defined.** Partition work into
    model/schema, repository/service, admin API, cart calculation, legacy-rule
    removal, and integration/regression phases. Each phase needs an explicit
    buildable test checkpoint and dependency order.

## Nit

Verification commands and README prerequisites are broad; specify exact Maven
profiles/modules and either document or explicitly exclude README changes.

## Checkpoint

Stage 9 is complete. The implementation-readiness result is not ready for
implementation until the blockers and major findings are resolved.
