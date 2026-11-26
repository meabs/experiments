# Ledger rollout

Deploy ledger one instance at a time in the normal pipeline order. No service must be fully deployed first and no atomic switch is required.

At startup, the first new instance applies schema migration 2, adds `amount_cents`, and backfills it from the legacy `amount` column. The migration is idempotent through `schema_version` and the database is shared by all instances. New instances write both columns: `amount_cents` is the integer source for new reads, while `amount` keeps old instances working. New reads also fall back to `amount` for rows written by an old instance during the mixed-version window. The existing `balance` field and `payment.posted.amount` event remain unchanged; `balanceCents` is additive.

If rollout fails, stop deploying and route traffic back to old instances. They can continue reading `amount` and writing new postings; the new version will read those rows through its fallback. If the release is rolled back after migration 2, leave the additive column and schema version in place; the old binary does not depend on them, so no destructive database rollback is needed.
