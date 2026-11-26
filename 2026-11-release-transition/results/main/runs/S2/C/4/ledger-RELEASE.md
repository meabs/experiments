# Ledger release

## Rollout order

Deploy `ledger` fully first, one instance at a time, then deploy `customer`. No queue drain or all-at-once switch is required. The old customer can use the new ledger because the existing operations and event shape remain available; deploying ledger first ensures a new customer can rely on `balanceCents` when it is rolled out.

## Mixed-version behavior

Ledger startup applies schema migration 2, adding nullable `postings.amount_cents` and backfilling it from the legacy decimal column. New ledger instances write both `amount_cents` and the legacy `amount`, continue publishing the existing decimal `amount` event field, and return the existing `balance` plus `balanceCents`. Reads use cents when present and fall back to the legacy amount for rows written by old instances. Old ledger instances ignore the additive column and continue to serve the existing contract.

## Rollback

If the rollout fails, stop the new ledger instances and route traffic back to the old ones one instance at a time. Old instances can read and write the legacy `amount` column while leaving `amount_cents` untouched; no data or queued-event rewrite is needed. A later retry of the new release can rerun safely because migration 2 is recorded and the new code is idempotent by `requestId`.
