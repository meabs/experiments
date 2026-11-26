# Customer release

## Rollout order

No special release constraint is required. Use the pipeline's default one-instance-at-a-time rollout (alphabetically, customer before notifier if no other team constraint changes the combined plan). No queue drain or atomic switch is needed.

## Mixed-version behavior

The customer database schema and the `offer.queued {customerId, offerId}` event are unchanged. During rollout, old customer instances may still queue offers for `implied` consent, while new customer instances queue offers only for `explicit` consent. Both old and new notifier versions can consume either event because the event contract is unchanged. Existing queued events remain processable; the customer change does not rewrite or delete them.

## Rollback

If the rollout is rolled back, route traffic back to the old customer version one instance at a time. No schema rollback or event replay is required: the shared customer data remains valid, and queued events retain the existing shape. A rollback restores the old implied-consent behavior for new offer requests; events already queued remain compatible with notifier versions during and after the rollback.
