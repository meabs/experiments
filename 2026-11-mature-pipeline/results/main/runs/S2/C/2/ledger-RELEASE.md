# Ledger release

## Rollout order

Deploy ledger instances one at a time in the normal pipeline order. No dependency on the customer rollout is required, and the services do not need an atomic switch or event drain.

The first new ledger instance runs schema migration 2 at startup. It adds `amount_cents` and backfills existing postings before serving requests. Later instances see the completed migration.

## Mixed versions

New ledger instances write both the legacy decimal `amount` and integer `amount_cents`. Old instances continue to write `amount`; new reads use `amount_cents` and fall back to converting `amount`, so either version can operate against the shared database. The existing decimal `payment.posted` event is unchanged, keeping both old and new customer versions compatible.

The balance response keeps `balance` and adds `balanceCents`. Consumers that only know the old response can ignore the additional field.

## Rollback

If rollout fails, stop and roll back the affected instances to the old ledger version. The old code can continue reading and writing the retained `amount` column, while rows written by the new version have that column populated as before. Leave schema version 2 and `amount_cents` in place; do not reverse the migration or delete data. A later retry can safely reuse the migrated database.
