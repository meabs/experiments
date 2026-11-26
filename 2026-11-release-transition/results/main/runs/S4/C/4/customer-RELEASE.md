# Customer CHG-104 rollout

## Rollout order

Deploy `customer` independently, one instance at a time. There is no ordering or atomic deployment constraint with `notifier`; the release pipeline may use its normal alphabetical order. Do not drain the event queue before deployment.

## Mixed-version behavior

The new customer version keeps the existing database tables, operations, and `offer.queued {customerId, offerId}` event contract. Old customer instances may still queue offers for legacy `implied` consent while they receive traffic; new instances queue offers only for `explicit` consent. Both notifier versions can consume either form of the unchanged event, and already queued events are retained and processable during the rollout.

## Rollback

If the rollout fails, stop promoting new customer instances and route traffic back to the old version. Leave the shared database and queued events in place; no migration or event rewrite is needed. Events emitted by either customer version remain compatible with both notifier versions. After rollback, the old version's implied-consent behavior may resume until it is redeployed or traffic is fully controlled.
