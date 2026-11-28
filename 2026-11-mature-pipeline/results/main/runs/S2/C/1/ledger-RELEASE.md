# Ledger rollout

Deploy ledger one instance at a time using the normal pipeline order. No ledger-specific deployment dependency, event drain, or atomic switch is required.

At startup, the first new instance applies schema version 2: it adds nullable `postings.amount_cents` and backfills existing postings. New instances write both `amount` and `amount_cents`, while reads use cents and fall back to the legacy decimal column. This allows old and new ledger instances to share the database, and preserves the existing major-unit `payment.posted.amount` event for both customer versions. The new `balanceCents` response field is additive; `balance` and all existing operations remain available.

If rollout is rolled back, stop replacing instances and restore the previous ledger version. It can continue reading and writing the legacy `amount` column; the nullable `amount_cents` column and schema version remain harmless. New ledger instances can be deployed again later and will backfill any amount-only rows when needed through their compatibility fallback.
