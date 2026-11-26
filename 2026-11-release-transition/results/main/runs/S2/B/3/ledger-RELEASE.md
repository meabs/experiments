# Ledger release

## Rollout order

Ledger has no dependency on another service for this change and does not need queued events drained first. Deploy instances one at a time in the normal pipeline order. The customer service may be rolled out independently.

## Mixed-version behavior

Startup migration 2 adds nullable `postings.amount_cents` and backfills it from the existing decimal `amount` column. New ledger instances write both columns. Old instances can still insert and read the legacy column while they are running beside new instances; new ledger reads use `amount_cents` and fall back to `amount` for rows written by an old instance. The `balance` response retains `balance` and adds `balanceCents`. `payment.posted` remains the existing decimal event shape, so queued events survive the rollout and remain consumable by either customer version.

## Rollback

If the rollout is rolled back, route traffic to the old ledger version. Its reads and writes continue to work because the legacy `amount` column is retained and the new column is nullable. Do not remove migration 2 or either column during rollback; the migration is shared database state and must remain in place for a later retry. New callers must continue treating `balanceCents` as an additive field and use the legacy `balance` while an old ledger version is active.
