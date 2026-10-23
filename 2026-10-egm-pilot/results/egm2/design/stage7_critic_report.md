# Stage 7 — Critic Review

## Findings

### Major — Heilmeier cost, timeline, and success exams are absent

The proposal has no engineering/operational cost estimate, timeline, or measurable mid-term and final acceptance metrics. Add effort and storage/runtime impact estimates, milestones, and explicit API, correctness, authorization, latency, and regression criteria.

### Major — Cart reads mutating persisted state create race and availability risks

Clearing invalid codes during reads can cause unexpected writes, lost updates, and database-failure behavior. Define transaction/concurrency semantics or make recalculation pure and perform cleanup through an explicit write path or job.

### Major — Store authorization is not a security contract

“Same authorization path” does not specify tenant derivation, IDOR prevention, or forbidden/not-found behavior. Define server-side principal-to-store checks for every CRUD operation and test forged store and discount IDs.

### Major — Uniqueness is race-prone without a concrete database strategy

“Database where supported” is insufficient. Specify the project’s migration/index strategy, handle unique-constraint races, and define trimming, case/Unicode normalization, and length limits.

### Major — Fixed-amount formulas and monetary precision are incomplete

State whether an amount applies once per cart, its cap at eligible subtotal, decimal scales, and rounding points. Add boundary tests for values below, equal to, and above eligible subtotal.

### Major — Date comparisons lack timezone and end-of-day semantics

Define UTC or store-timezone comparison, end-date interpretation, DST/midnight behavior, and boundary tests.

### Major — Category resolution may be expensive and inconsistent

Define descendant queries, deleted/moved category behavior, indexing, cycle handling, and performance targets to avoid recursive N+1 work on every cart read.

### Major — Mutable discount definitions conflict with checkout history

Specify foreign-key/delete behavior, concurrent checkout handling, and immutable order totals or snapshots so later edits cannot change an order’s recorded discount.

### Major — Legacy rule and shared calculation ownership are unclear

The plan could double-apply discounts or leave `Test1234` active because it says “replace or remove” without naming the authoritative module and invocation order. Define one path and regression proof for exactly-once application.

### Nit — Listing and DTO limits are unspecified

Define pagination/filtering, validation limits, and a stable error schema to avoid unbounded responses and inconsistent clients.

### Nit — Display spelling source of truth is unclear

Specify whether cart responses use the current code spelling or an application-time snapshot when a code is renamed.

## Stage Result

The design has material security, lifecycle, calculation, and operational gaps. It should not advance to implementation-readiness review without explicit contracts and risk mitigations.

