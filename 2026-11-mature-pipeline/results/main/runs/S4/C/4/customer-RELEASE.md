# Customer release

## Rollout order

1. Drain queued `offer.queued` events.
2. Switch all customer and notifier instances atomically to their new versions, with no traffic between versions.

The atomic switch is required because old customer instances still know how to emit offers for implied-consent customers. A one-at-a-time customer rollout would therefore allow such an offer after the new consent rule had taken effect. Draining first limits work from the old release, while the atomic switch prevents new old-version effects during the transition.

## Mixed-version behavior

The `offer.queued` event remains `{customerId, offerId}` and the persistent customer schema is unchanged. During the switch there is no mixed customer/notifier traffic: the new customer publishes only for `explicit` consent, and the new notifier applies its daily cap. Existing queued events remain valid for the new notifier.

## Rollback

If the rollout fails, stop it and atomically restore both services to their previous versions, with no traffic between versions. Do not roll back customer independently: that would re-enable implied-consent effects against the new notifier. Existing queued events remain processable, so no data rewrite or queue purge is required.
