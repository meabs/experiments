# Release plan

## Rollout order

Switch `customer` and `ledger` as one atomic release group. All instances of
both services must be switched together, with no traffic between old and new
versions during the cutover. Process or otherwise account for queued
`payment.posted` events before completing the cutover.

## Mixed-version behavior

The new customer read model stores balances as minor units and reads the new
`amountMinor` event field. It also accepts the retired decimal `amount` field,
so events already queued by old ledger instances remain usable during a
transition. An old customer instance is not compatible with a new ledger event
that contains only `amountMinor`; that is why the release group is atomic.

## Rollback

If validation fails, stop the group and roll back customer and ledger together
before resuming traffic. Do not roll back customer alone after any new
minor-unit-only event has been published. Preserve the shared databases and
queued events; the old customer can consume only legacy decimal events, so a
rollback must occur before new-format events are delivered to old instances,
or those events must be drained/handled by the new customer before reverting.
