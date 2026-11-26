# Ledger rollout

## Order

Deploy ledger one instance at a time using the normal pipeline order. No service needs to be fully deployed first and no atomic cutover is required. The schema migration runs when the first new ledger instance starts; later instances observe schema version 2.

## Mixed versions

The migration adds nullable `postings.amount_cents` and backfills it from the existing decimal `amount`. New ledger instances write both columns and continue publishing `payment.posted.amount` as the existing decimal string, so old customer instances and queued events remain compatible. Reads use `amount_cents` and fall back to the decimal column for rows written by an old ledger instance. `balanceCents` is an additive response field; the existing `balance` field and all existing operations remain unchanged.

## Rollback

If rollout fails, stop new ledger instances and route traffic back to the previous version one instance at a time. The previous version ignores the added column and can keep writing decimal amounts; those rows are handled by a later new version through the fallback and migration data remains intact. Do not remove schema version 2 or `amount_cents`; the migration is intentionally forward-compatible and the database and queued events are retained.
