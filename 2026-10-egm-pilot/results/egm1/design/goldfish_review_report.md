# Goldfish Annotated Review Report

**Status:** resolved

**Target:** `design_draft.md` (`full file`)

## Prioritized Findings & AI Suggestions

### Issue 1 — Approved status conflicts with unresolved architecture [egm-design] — Severity: High

* **Affected Scope:** Open Questions, Technical Plan, Detailed Implementation Plan
* **Discrepancy Description:** The document is marked Approved while persistence ownership, migration, cart response compatibility, category queries, and authorization remain open.
* **AI Suggestion:** PROPOSE FIX
* **Justification:** Approval should follow resolution of implementation-defining choices.
* **Proposed Edit:** Change status to `In Review` and retain open questions until concrete decisions are documented.

### Issue 2 — Reuse existing pricing pipeline [egm-zoom-out/egm-design] — Severity: High

* **Affected Scope:** Technical Plan and implementation items 2 and 5
* **Discrepancy Description:** A parallel eligibility/calculation path is proposed despite existing promo, shopping-cart calculation, order-total, and readable-cart components.
* **AI Suggestion:** PROPOSE FIX
* **Justification:** Reusing one pricing seam avoids duplicate discounts and inconsistent cart/order totals.
* **Proposed Edit:** Name the existing pricing components as the integration point and state that the new lookup replaces the rules-backed calculation there.

### Issue 3 — Complete API and validation contracts [egm-design/egm-comprehension/egm-style] — Severity: High

* **Affected Scope:** Goals, Admin API, validation, Open Questions
* **Discrepancy Description:** JSON schemas, normalization, PUT semantics, pagination, not-found behavior, malformed IDs, authorization errors, and validation matrix are absent.
* **AI Suggestion:** PROPOSE FIX
* **Justification:** These are observable contracts required for independent implementation and testing.
* **Proposed Edit:** Add an endpoint/schema table and explicit validation/default/error rules.

### Issue 4 — Define eligibility, totals, and date semantics [egm-design/egm-comprehension] — Severity: High

* **Affected Scope:** Eligibility service, CUJs, money correctness
* **Discrepancy Description:** Price/subtotal basis, tax/shipping treatment, discount sign, timezone, date source, category matching, and currency precision are unspecified.
* **AI Suggestion:** PROPOSE FIX
* **Justification:** Different interpretations change the amount charged and eligibility at boundaries.
* **Proposed Edit:** Add exact formulas, processor ordering, timezone, category rules, and worked examples.

### Issue 5 — Define cart persistence and concurrency [egm-design/egm-comprehension] — Severity: High

* **Affected Scope:** Cart application/presentation and consistency requirements
* **Discrepancy Description:** The stored cart field and behavior for rename/delete/concurrent read/apply/edit are unspecified; clearing during GET is a write.
* **AI Suggestion:** PROPOSE FIX
* **Justification:** Without state and transaction rules, carts can show stale or contradictory totals.
* **Proposed Edit:** Choose code text versus discount id, define lifecycle, idempotent invalidation, and transaction/versioning behavior.

### Issue 6 — Make migration and uniqueness portable [egm-design] — Severity: High

* **Affected Scope:** Persistence and migration plan
* **Discrepancy Description:** The migration location, supported databases, legacy data, rollback, and constraint-exception mapping are not specified.
* **AI Suggestion:** PROPOSE FIX
* **Justification:** Schema and 409 behavior must work under the repository’s actual database setup.
* **Proposed Edit:** Identify the project schema mechanism and exact uniqueness/rollback approach.

### Issue 7 — Expand alternatives and risk structure [egm-design/egm-structural] — Severity: High

* **Affected Scope:** Alternatives and Non-Functional Requirements
* **Discrepancy Description:** Viable persistence/calculation/category alternatives are missing, and risks are not in a dedicated section.
* **AI Suggestion:** PROPOSE FIX
* **Justification:** The feature-spec standard requires documented alternatives, risks, and mitigations.
* **Proposed Edit:** Add the alternatives and a Risks & Mitigations section with failure modes and bounds.

### Issue 8 — Define concrete terms and measurable constraints [egm-comprehension/egm-style] — Severity: Medium

* **Affected Scope:** Technical Plan and Non-Functional Requirements
* **Discrepancy Description:** Store resolution, category descendants, readable-cart mapper, cart-returning endpoints, and “bounded category data” are unexplained or vague.
* **AI Suggestion:** PROPOSE FIX
* **Justification:** A fresh engineer cannot implement or verify these statements without guessing.
* **Proposed Edit:** Add definitions, concrete route/component names, query bounds, and measurable acceptance criteria.

### Issue 9 — Structural and style cleanup [egm-structural/egm-style] — Severity: Low

* **Affected Scope:** Headings, traceability, Markdown formatting
* **Discrepancy Description:** “The Problem” is not the standard heading, no traceability matrix exists, and list formatting is inconsistent.
* **AI Suggestion:** PROPOSE FIX
* **Justification:** These changes improve auditability without changing behavior.
* **Proposed Edit:** Rename the heading, add requirement-to-CUJ-to-test mapping, and standardize lists.

### Issue 10 — README malformed demo link [egm-structural] — Severity: Low

* **Affected Scope:** `README.md`
* **Discrepancy Description:** An unrelated README demo link is malformed.
* **AI Suggestion:** CONTEST
* **Justification:** It is outside the target design document and feature scope; changing it would broaden the review.
* **Proposed Edit:** None.

## Resolution Gate

Review the proposed classifications and edits. Reply `auto accept` to apply all
PROPOSE FIX items, `continue` to apply none, `interactive breakdown` for
item-by-item decisions, or provide a custom instruction.
