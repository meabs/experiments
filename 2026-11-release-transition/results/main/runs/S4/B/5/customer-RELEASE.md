# Customer CHG-104 rollout

## Rollout order

There is no dependency on notifier's deployment and no requirement for an atomic switch or event drain. The pipeline may use its default alphabetical, one-instance-at-a-time rollout. This is safe to do independently of notifier's daily-offer-cap change.

## Mixed-version behavior

The new customer version changes only the marketing decision: `consent.check` and `offer` allow marketing only for `explicit` consent. `none` and legacy `implied` consent return `allowed=false` and `queued=false`.

Old customer instances may continue to queue offers for `implied` customers until they are replaced, while new instances will not. Both versions use the same existing `offer.queued {customerId, offerId}` event, so old and new notifier instances can consume events from either customer version. Existing database rows and queued events require no migration or replay.

## Rollback

If the customer rollout is rolled back, stop replacing instances and restore the previous customer version one instance at a time. The unchanged schema, event topic, and event fields remain compatible, and no database rollback or queue drain is required. A rollback can re-enable implied-consent offers on instances running the old version; after rollback, monitor the rollout until all instances are on the selected version.
