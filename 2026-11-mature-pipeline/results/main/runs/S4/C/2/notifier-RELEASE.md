# Notifier rollout

1. Drain the existing `offer.queued` queue before starting the rollout.
2. Deploy notifier instances one at a time, waiting for `health` after each instance. Keep the existing customer rollout independent; both customer versions publish the unchanged `offer.queued {customerId, offerId}` event.
3. Once a new notifier instance is healthy, route new offer events to new instances. This avoids sending fresh events to an old notifier while old and new binaries overlap.

The new version creates the additive `offer_daily` table and retains the existing `sent` table. New instances lock one customer/day row and count existing `sent` rows, so multiple new instances enforce a shared limit of two sent offers per platform day. `sent` responses retain `count` and `ticks` and add cumulative `capped`; `capped` is zero when no offers have ever been dropped. Old customer instances remain compatible because the event contract is unchanged.

If the rollout fails, stop routing events to new notifier instances and restore the previous notifier binary. Keep both tables and all rows. The old version can read the existing `sent` table, and the new version can be redeployed later; any offers accepted by old instances during rollback are preserved as sent history. Because the old binary does not enforce the new cap, rollback should be completed promptly and the release owner should reconcile any events processed by old instances before retrying the rollout.
