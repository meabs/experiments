# Customer CHG-104 rollout

## Rollout order

Customer and notifier are an atomic release group. Switch all instances of both services together, with no test traffic between the old and new versions. There is no safe one-instance-at-a-time order for this change: an old customer instance can otherwise publish an implied-consent offer after the new consent rule is active.

## Mixed-version behavior

After the atomic switch, customer returns `allowed=false` for `implied` consent and does not publish an event for that customer. It continues to publish the existing `offer.queued {customerId, offerId}` event for `explicit` consent. Because the switch is atomic, there is no traffic window in which old customer behavior is paired with the new release. The event shape is unchanged, so events already queued by the old release remain consumable by the new notifier.

Events already queued before or during rollout are not rewritten or removed. They are processed by whichever notifier version receives them, subject to that version's normal behavior.

## Rollback

If the rollout fails, roll back the atomic group together before resuming traffic. This restores the old customer and notifier versions consistently; no database migration or event replay is required. Events already queued remain valid and may be processed by the restored notifier. Do not roll back only one service, since that would recreate the mixed-rule window.
