# Customer / CHG-101 rollout

## Rollout order

Drain the queued events before deployment. Then deploy and switch `customer`
and `ledger` atomically, with no traffic between the old and new pairs. They
must be treated as one rollout unit; there is no `deploy_after` ordering within
the pair.

## Mixed-version and data behavior

The new customer reads `amountMinor` as the authoritative value and also reads
the legacy decimal `amount` field. This lets it consume events already stored
in the queue before the switch. The statement table remains in minor units, so
existing balances are preserved and new events update the same read model.

An old customer must not receive a new ledger event: it cannot read
`amountMinor`. The atomic switch prevents that mixed-schema traffic while the
new pair is being introduced.

## Rollback

Do not roll back either service independently. First stop the new pair from
producing traffic and drain all queued `amountMinor` events with the new
customer. Then atomically restore both old versions. The restored customer can
process any remaining legacy events; its shared statement data is retained.
