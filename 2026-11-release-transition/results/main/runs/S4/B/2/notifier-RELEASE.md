# Notifier rollout

Deploy the customer change independently; notifier has no synchronous dependency on customer and both versions publish/consume the same `offer.queued {customerId, offerId}` event. Before each notifier instance is changed, drain queued `offer.queued` events, then deploy notifier instances one at a time and verify `health` and `sent`.

During the rollout, old and new notifier instances share the existing `sent` table. The new version adds `offer_daily` and leaves `sent` unchanged, so old instances can continue to process events and both versions can read the database. New instances enforce two sends per customer per platform day (`tick / 100`) and report dropped offers in `capped`; queued offers remain additive and unchanged. The drain-before step prevents already queued work from straddling a rollout step.

To roll back, stop the new instance and restore the previous notifier version one instance at a time. Keep `offer_daily` and `sent` intact; the old version ignores the additive table and continues reading the original `sent` contract. Because the old version does not enforce the new cap, rollback restores legacy sending behavior until the new version is redeployed.
