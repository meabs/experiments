# Customer release

## Rollout order

Deploy customer one instance at a time in the normal pipeline order. No dependency on notifier deployment is required, and no atomic switch or queue drain is required. The published operation shapes and `offer.queued` event shape are unchanged.

## Mixed-version behavior

While old and new customer instances run together, old instances continue to treat legacy `implied` consent as marketing-eligible, while new instances require `explicit` consent. Both versions continue to return the same `consent.check` and `offer` response shapes. New instances publish the same `offer.queued {customerId, offerId}` event as before, and old instances consume no customer events. Existing queued events remain valid for either notifier version, including the notifier's concurrent daily-cap rollout.

## Rollback

If the rollout fails, stop promoting the new customer version and route traffic back to the previous version one instance at a time. No database migration needs reversing and no queued events need rewriting or draining. The previous version can resume queuing offers for `implied` consent; notifier versions remain compatible because the event contract is unchanged.
