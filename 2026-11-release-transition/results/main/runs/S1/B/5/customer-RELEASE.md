# Release plan

## Rollout order

Drain the queued `payment.posted` events, then prepare and switch all customer and
ledger instances as one atomic release. There must be no interval in which new
ledger instances publish to old customer instances. The customer can be deployed
and smoke-tested against the old ledger before the switch because it accepts both
event formats, but traffic is switched only with the matching ledger release.

## Mixed-version behavior

The new customer read model stores balances as minor-unit `BIGINT` values. It reads
the new ledger event field `amountMinor` and also accepts the retired decimal
`amount` field while older queued events are being delivered. This makes a new
customer safe beside an old ledger. The atomic switch is still required because an
old customer cannot process an `amountMinor`-only event from a new ledger.

## Rollback

If the release fails, stop the switch and keep both services on their old versions.
If the new versions have already processed events, first drain the queue, then
switch customer and ledger back together. Do not roll back customer alone after a
new ledger has published `amountMinor` events: old customer code cannot consume
those events. Preserve the database and queue contents; the old ledger remains
idempotent by request ID, and any replayed legacy events are handled by the new
customer before the rollback.
