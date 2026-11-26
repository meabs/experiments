# Ledger rollout

Deploy ledger one instance at a time in the normal pipeline order. No dependency on customer being fully deployed is required: the schema change is additive, and the existing `payment.posted` event remains unchanged. No queue drain is required.

On first startup of a new instance, schema migration 2 adds `postings.amount_cents` and backfills existing rows. New ledger instances write both `amount` and `amount_cents`, publish the existing major-unit `amount` event, and return the existing `balance` plus `balanceCents`. During mixed operation, old instances continue to read and write `amount`; new instances use `amount_cents` and fall back to `amount` for rows created by old instances. Customer therefore continues to consume events normally.

If rollout fails, stop the new instances and roll back to the old version. The legacy `amount` column and event format remain populated, so old instances continue serving balances and posting requests. The additive column and schema version can remain in the database; a later retry can reuse them.
