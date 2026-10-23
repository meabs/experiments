# Stage 7 — Critic Review

Target: `design_draft.md` FeatureRange (lines 1–359)
Reviewers: `egm-design`, `egm-structural`, `egm-style`
Standard: `feature-spec-standard.md`

## Design Critic Findings

### Major — Schema rollout is unsafe for existing databases

**Scope:** lines 116–126.

The design rejects a versioned migration and relies on
`hibernate.hbm2ddl.auto=update`, but does not define safe creation of the
normalized column, category table, indexes, uniqueness constraint, or handling
of conflicting legacy data. Define deployment ordering, backfill/validation,
and rollback behavior.

### Major — Unbounded admin/read-path work

**Scope:** lines 150–152 and 212–239.

Collection GET is unpaginated, and every cart read reloads the discount and
resolves each category with `CategoryService.getByCode`. Unbounded records and
category lists can create large responses and N+1 database work. Define
reasonable limits and bulk-fetching/indexing or another bounded lookup strategy.

### Major — Date source is nondeterministic across nodes

**Scope:** lines 76–82, 202–203, 216–219.

Server-local `LocalDate.now()` can differ across JVM time zones or clocks,
causing inconsistent activation and expiry. Define one authoritative timezone or
clock abstraction shared by defaults and evaluation, and test boundaries.

### Major — Minimum-subtotal basis is ambiguous

**Scope:** lines 218–245 and 279–284.

The document does not clearly state whether `minimumSubtotal` uses the full cart
subtotal or the eligible subtotal for restricted discounts. Define the exact
basis, ordering, and category-restricted examples.

### Major — Apply/save concurrency is unspecified

**Scope:** lines 250–278.

Pricing/evaluation and cart-code persistence are separate operations with no
transaction or optimistic-lock behavior. Concurrent cart changes or merchant
edits could produce stale eligibility or overwrite state. Define transaction
boundaries/version checks and response behavior.

### Major — Tax and variation interaction needs an invariant

**Scope:** lines 281–301.

The merchant discount is applied around legacy variations while the tax module's
base is deliberately unchanged. This can display tax on an undiscounted base
while subtracting the discount from the total, and negative/zero post-variation
subtotals are not fully constrained. State the legal/business tax choice and
non-negative invariants with tests.

### Nit — Acceptance measures and alternatives are thin

**Scope:** lines 55–88 and 340–358.

The document has no measurable success or performance criteria, and alternatives
cover only two storage/calculation choices. Add acceptance measures and assess
operational alternatives such as paginated admin results or precomputed
category eligibility.

## Structural Finding

### Major — Missing explicit Risks & Mitigations section

**Scope:** document structure, lines 1–359.

The feature standard requires a dedicated treatment of failure modes, security,
scalability limits, constraints, and mitigations. Risks are scattered through
the architecture text but there is no explicit section.

## Style Findings

### Major — “Code” is overloaded

**Scope:** lines 31, 52, 67–75, 83–85, 231–239, 246–247.

Use distinct terms such as “discount code,” “promo input,” and “category code.”
In particular, replace “restricted code” when the text means a category code.

### Major — Bullets combine too many concerns

**Scope:** lines 147–168, 169–187, 210–249, 250–301.

Split long bullets so API behavior, validation, implementation details, and
rationale are separately identifiable normative requirements.

### Major — Vague repository references

**Scope:** lines 156–160, 198–208, 330–334.

Name concrete classes/files instead of “existing private API layers,”
“controller-facade bridge pattern,” and “processor Spring configuration.”

### Nit — Exception paragraph has a malformed fragment

**Scope:** lines 139–143.

Remove the stray closing parenthesis after `ServiceException` and complete the
“beside the existing” sentence.

### Nit — Informal status phrasing

**Scope:** lines 31 and 174–176.

Replace “a new code returns HTTP 400” and “fail ... into a 500” with direct
request/application status language.

### Nit — Approximate line references are brittle

**Scope:** lines 312 and 319–325.

Use method names and behaviors instead of “around line” references.

### Nit — Subjective comparisons

**Scope:** lines 344 and 354–358.

Replace “clearer” and “would not reliably affect” with concrete properties such
as fewer execution paths, explicit store scoping, or guaranteed invalidation.
