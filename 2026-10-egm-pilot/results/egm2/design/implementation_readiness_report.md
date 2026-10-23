# Stage 9 — Implementation Readiness Test

## Findings

### Major — Persistence and migration choices remain open

The plan uses wildcard migration paths and “migration mechanism to match the project,” but this repository has no `db/migration` tree and uses Hibernate schema update. Exact tables, columns, ORM mappings, indexes, nullability, foreign keys, and rollback/compatibility behavior must be specified.

### Major — API and DTO contracts are not executable

Wildcard packages and phrases such as “complete resource” and “paginated list” omit exact module, class/package, field types, JSON names, nullability, pagination envelope, route signatures, and error payloads.

### Major — Existing cart and promo pipeline integration is incomplete

The plan does not explicitly modify `ShoppingCartCalculationServiceImpl`, the order-total pipeline, or `ProcessorsConfiguration`, even though those components currently calculate totals and register `PromoCodeCalculatorModule`. A fresh implementer could leave duplicate or stale paths.

### Major — Cart persistence model is undefined

The current cart stores only `promoCode` and `promoAdded`; the clarification requires a discount ID/reference and display spelling. Field types, ORM mapping, deletion behavior, and service signatures are not specified.

### Major — Tests are not first-attempt actionable

Wildcard test paths and “related cart tests” omit exact classes, fixtures, assertions, JSON/error bodies, migration checks, concurrent duplicate creation, and required Maven commands.

### Major — Contradictory lifecycle instructions

The plan says cart reads clear invalid references, while the clarification says reads do not mutate and explicit writes clear them. One sequence and transaction rule must be selected.

### Major — Alternative architecture wording remains

“Removed or disabled,” “replace or remove,” and “removing or deprecating as appropriate” leave multiple implementations open. Specify one required legacy-rule outcome and one timestamp-field migration outcome.

### Nit — Limits and metrics lack numeric definitions

Code length, category count, page size, stable error codes, latency budget, currency source, and test commands need fixed values and acceptance thresholds.

## Stage Result

The implementation plan fails the zero-decision rule. It requires a concrete repository-aligned schema/API contract and exact integration/test instructions before implementation can begin without additional design decisions.

