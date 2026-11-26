# Customer release

## Rollout order

Customer and ledger are one atomic release group. Switch all instances of both
services together, with no traffic delivered between the old and new versions.
There is no independent one-instance rollout order for this change: the atomic
boundary is required because new ledger events contain `amountMinor`, while the
old customer only understands `amount`.

## Mixed-version behavior

The new customer reads `amountMinor` as an integer number of minor units and
also accepts legacy `amount` events. This lets it consume events already in the
queue from old ledger instances. The new ledger must not be exposed to old
customer instances; the atomic switch prevents that incompatible combination.
The statement table remains in minor-unit (`balance_cents`) storage, so existing
balances remain unchanged.

## Rollback

Stop the atomic release group and drain the payment event queue with the new
versions before exposing old versions. Then revert customer and ledger together,
with no traffic between versions. Draining first is required because queue
contents survive deployment and an old customer cannot consume a retained
`amountMinor`-only event. If the queue cannot be drained, keep the new customer
and ledger versions running and do not perform a partial rollback.
