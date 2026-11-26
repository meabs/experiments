# Customer rollout

## Order

First drain the event queue so all offers created under the old consent rule have been processed. Then switch all `customer` and `notifier` instances together, with no traffic between the old and new pair. The atomic boundary is required because an old customer instance can still queue an offer for an `implied` customer.

## Mixed-version behavior

The customer contract and the `offer.queued {customerId, offerId}` event shape are unchanged. After the drain, the atomic switch ensures that customer and notifier are either both old or both new; there is no mixed-version traffic window. New customer instances allow marketing only for `explicit` consent and do not queue offers for `implied` or `none`. The notifier daily-cap change remains compatible with the unchanged event shape.

Queued events are retained and may be delivered after either deployment, so consumers must continue accepting the unchanged event shape.

## Rollback

If the rollout fails, roll back the `customer` and `notifier` pair together, preserving the atomic boundary. Do not roll back only customer or only notifier, because that would reopen the mixed-version window. The drain is repeatable before a retry, no schema or event migration is needed, and the unchanged event shape remains consumable by either notifier version. Existing database contents are retained.
