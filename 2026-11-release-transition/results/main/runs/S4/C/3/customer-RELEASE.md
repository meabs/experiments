# Customer release

## Rollout order

Deploy `customer` and `notifier` as one atomic release, switching all instances
together with no traffic between the old and new versions. Do not use the normal
one-instance-at-a-time rollout for this pair.

## Mixed-version behavior

The customer database schema is unchanged, and old and new customer versions use
the same `offer.queued {customerId, offerId}` event contract. The event remains
valid for either notifier version. A mixed customer rollout is intentionally not
allowed: an old customer could still queue an implied-consent offer while the new
rule is active. Events already queued before the switch remain durable and are
processed normally; no queue drain is required.

## Rollback

If either service fails its rollout, roll back both services as one atomic switch
before routing traffic to the old versions. No schema or event migration is
needed. Rollback does not remove already queued or sent offers; those durable
records remain valid and the unchanged event format is accepted by both notifier
versions.
