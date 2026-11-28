# Customer release: CHG-104

## Rollout order

Prepare the new customer and notifier instances using the normal one-instance-at-a-time startup checks, but do not route traffic to either new version yet. Once every instance in both services is ready, drain the queued `offer.queued` events and confirm the queue is empty. Then switch all customer and notifier instances together. There must be no traffic interval with only one service switched.

## Mixed-version behavior

While new instances are being prepared and the queue is draining, all routed traffic remains on the old pair: old customer instances may still treat `implied` consent as eligible, and old notifier instances process the resulting `offer.queued {customerId, offerId}` events. After the queue is empty, the atomic switch changes both services together. New customer instances then allow and queue offers only for `explicit` consent, while the new notifier handles the same event shape.

## Rollback

If any customer or notifier instance fails startup or health checks, abort before the drain/cutover and keep both services on their old versions. If failure occurs after switching, switch both services back together; never roll back only one of them. No database or event cleanup is needed: the schema and event contract are unchanged, and any newly queued offers can be consumed by either notifier version.
