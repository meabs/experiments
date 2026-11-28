# Release plan

## Rollout order

First drain the existing event queue while the old pair is running. Then
switch `customer` and `ledger` atomically, with all instances switched at
once and no traffic between the old and new pair. The queue is retained; the
new customer can consume both the new and legacy event shapes.

## Mixed-version behaviour

The new customer reads `amountMinor` as the statement balance's minor-unit
value. It also falls back to the legacy decimal `amount` field, so events
already queued by an old ledger remain processable. The new ledger emits
`amountMinor`; atomic switching prevents an old customer from seeing an
amountMinor-only event. Other customer operations are unchanged.

## Rollback

To roll back, stop new payment traffic, let the new customer drain all
`payment.posted` events (including amountMinor events), and then switch both
services atomically back to the previous pair. Do not roll back only one
service or leave amountMinor events queued: an old customer cannot consume
an amountMinor-only event from a new ledger.
