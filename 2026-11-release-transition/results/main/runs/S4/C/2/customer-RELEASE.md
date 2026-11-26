# Customer release

## Rollout order

First drain all queued `offer.queued` events. Then switch every customer and notifier instance together, with no traffic between the old and new versions. The services are therefore released as one coordinated cutover rather than one instance at a time.

## Mixed-version behavior

Before the cutover, any queued offers are processed under the old behavior. After the drain, there is no mixed customer/notifier traffic window: new customer instances allow and publish `offer.queued {customerId, offerId}` only for `explicit` consent, while the new notifier applies its daily cap to that unchanged event. The additive event shape remains readable by the old notifier if rollback is needed.

## Rollback

If the coordinated switch fails, keep the old pair serving and roll back/retry both services together; never leave only one service switched. The queue was drained before the switch, and the existing `offer.queued` payload is unchanged, so rollback does not require a schema migration or event transformation. Old customer behavior may again queue implied-consent offers after rollback, but those offers are processed only after the old pair is serving again.
