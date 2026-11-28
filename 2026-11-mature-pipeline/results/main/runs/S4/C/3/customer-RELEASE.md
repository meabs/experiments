# Customer release: CHG-104

## Rollout order

Deploy customer independently, one instance at a time. There is no required ordering with notifier, no atomic switch, and no queue drain. If the release pipeline has no other constraints, normal alphabetical service ordering applies. The first new customer instance performs the shared-database compatibility migration before serving traffic.

## Mixed-version behavior

The new customer version considers marketing consent allowed only when the stored basis is `explicit`. It returns `allowed=false` for `implied` and does not publish an offer for those customers. Startup changes the effective legacy value from `implied` to `none`, retaining `implied` as `consent_basis`; a database trigger applies the same translation to two-column inserts from old customer instances. It keeps the existing `offer.queued` event and its `{customerId, offerId}` fields unchanged.

While versions overlap, old customer instances see `none` for migrated or newly inserted legacy customers and therefore cannot publish those offers. Explicit-consent offers continue to work with both notifier versions, including the notifier's daily cap behavior.

## Rollback

Rollback customer instances independently, one at a time. The additive consent-basis column and compatibility trigger remain valid for old binaries, so rollback cannot re-enable legacy offers; explicit consent and all event schemas remain unchanged. The notifier can remain on either version, and queued events remain consumable. If a partial rollout is rolled back, allow in-flight requests to finish and then continue normal traffic; no queued-event drain is needed.
