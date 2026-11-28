# Ledger rollout

Deploy the new ledger instances one at a time, preferably completing ledger before deploying the customer change that consumes `balanceCents`. No queue drain or atomic switch is required.

The startup migration advances `schema_version` to 2, adds nullable `postings.amount_cents`, and backfills existing rows. Nullability is intentional: an old ledger instance can still write the legacy `amount` column while a new instance is running. New writes populate both columns. New reads use `amount_cents` and fall back to `amount * 100`, so either version can serve traffic during a partial rollout. The payment event remains unchanged and continues to carry the major-unit `amount`, preserving compatibility with old and new customer consumers.

To roll back, stop new ledger instances and redeploy the previous version. It continues to read and write `amount`; the extra nullable column and schema version are harmless to it. Keep the migrated database and events in place. Any new ledger rows already written have the legacy `amount` value, so the old version can read them and continue idempotent processing. Redeploy the new version later to resume serving `balanceCents`.
