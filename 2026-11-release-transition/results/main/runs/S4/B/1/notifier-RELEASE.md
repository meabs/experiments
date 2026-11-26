# Notifier rollout

## Rollout order

Switch all customer and notifier instances together, with no traffic between the old and new versions (`atomic_with: [customer]`). This is required because the old notifier does not enforce the daily cap. No queue drain is required: queued `offer.queued` events retain the existing `{customerId, offerId}` shape and can be processed by either version.

## Mixed-version and rollback behavior

The new notifier adds the `offer_daily` table and leaves the existing `sent` table and event contract unchanged. Its `sent` response is additive: existing `count` and `ticks` remain unchanged, with `capped` added. Both customer versions can therefore produce events accepted by the notifier versions, and consent changes do not alter the event shape.

If the rollout fails, switch the atomic group back together. The old notifier ignores `offer_daily` and continues to read the existing `sent` data. Rollback restores the old behavior for subsequent events; already sent rows and cap counters remain in the database and are not deleted.
