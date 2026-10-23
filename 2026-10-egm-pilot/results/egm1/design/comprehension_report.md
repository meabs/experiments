# Stage 6 — Comprehension Test

*Target:* [design_draft.md](~/code/benchmark/skills-impact-work/egm-runs/egm1/repo/design_draft.md)

## Findings

### Major — Define store identity and resolution

**Affected scope:** Overview, Goals, Technical Plan (`store`, `store-scoped`,
`MerchantStore`, and `?store=`).

The draft does not define the store identifier, how it maps to `MerchantStore`,
or how request store context is established. A fresh engineer cannot determine
the request format or tenancy boundary from the document.

### Major — Specify JSON schemas and update semantics

**Affected scope:** Goals, CUJ 1, Admin API.

The promised JSON shape is not reproduced with field types, required/optional
fields, defaults, or PUT semantics. Status-code behavior cannot be implemented
or verified unambiguously.

### Major — Define normalization and database behavior

**Affected scope:** Data and service layer; Admin API.

“Normalized lookup form” and case-insensitive uniqueness do not define trimming,
Unicode/case rules, collation, or supported-database behavior. The design needs a
portable normalization and constraint strategy.

### Major — Define timezone and date source

**Affected scope:** Eligibility service, CUJ 2, Non-Functional Requirements.

“Today” and inclusive boundaries lack a timezone and clock source. UTC, server
time, and store-local time can produce different eligibility at midnight.

### Major — Define applied-code persistence and lifecycle

**Affected scope:** Cart application and presentation; implementation item 5.

“Persist only the applied code reference/value” does not identify the cart field,
whether it stores code text or an entity id, or how rename/delete affects an
existing cart.

### Major — Explain existing cart response and totals contracts

**Affected scope:** Cart application and presentation; CUJs 2–3.

Terms such as “readable-cart mapper,” “positive discount total line,” and
“total” are assumed knowledge. No response example, total-line schema, or
explanation of how a positive discount interacts with the existing totals model
is provided.

### Major — Define category matching precisely

**Affected scope:** Data and service layer; CUJ 2; Non-Functional Requirements.

The draft does not define multiple-category products, parent-category inclusion,
category assignment representation, or duplicate counting. These assumptions
change discount totals.

### Major — Explain authorization prerequisites

**Affected scope:** Admin API; Security and tenancy requirements.

“Existing private API authentication” and store checks are external prerequisites
without a local explanation or link. Required roles, permissions, and denied
store-access behavior are unspecified.

### Nit — Identify the legacy rules mechanism

**Affected scope:** Overview, Non-Goals, Verification Plan.

The rules file and `Test1234` path are not located or described, making removal
and regression expectations ambiguous to a new reader.

### Nit — Clarify currency precision

**Affected scope:** Money correctness; CUJ 2.

“Store’s currency scale conventions” is undefined and its interaction with
mandatory two-decimal discount rounding is unclear.

### Nit — State test prerequisites

**Affected scope:** Verification Plan.

The proposed commands assume Maven, database setup, and module test conventions
that are not documented, so a fresh engineer cannot reproduce the verification
steps.

## Checkpoint

Stage 6 is complete. The next stage must not begin until these findings are
accepted or revision instructions are provided.
