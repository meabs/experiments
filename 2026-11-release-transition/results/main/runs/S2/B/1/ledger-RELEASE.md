# Ledger CHG-102 rollout

## Rollout order

No service dependency requires an ordering constraint, so the pipeline may roll out ledger one instance at a time (and may roll it out before or after customer). The first new instance runs schema migration 2 at startup; later instances observe the completed migration.

## Mixed-version behavior

Migration 2 adds `postings.amount_cents` and backfills it from the existing decimal `amount`. New ledger instances write both columns and return the existing `balance` plus additive `balanceCents`. They continue publishing `payment.posted.amount` as a decimal string, so existing customer instances continue to consume events. During a mixed rollout, an old ledger instance may write only `amount`; new reads fall back to that column when `amount_cents` is null.

## Rollback

If the rollout fails, stop new instances and route traffic back to the old version. The old version ignores the additive column and continues to read and write `amount`; data written by the new version remains readable because it also writes `amount`. The schema migration is intentionally forward-compatible and is not rolled back. If the new version is redeployed later, it will backfill any legacy rows whose `amount_cents` is still null.
