# Notifier rollout

Deploy notifier instances one at a time; no dependency on customer deployment order is required. The old and new customer versions both publish the same `offer.queued {customerId, offerId}` event.

The new notifier creates the additive `offer_daily` table and seeds it from existing `sent` rows. During a mixed rollout, old notifier instances continue to send using the existing table while new instances enforce two sends per customer per platform day (`floor(tick / 100)`) and count dropped offers. The `sent` response keeps `count` and `ticks` and adds `capped`.

If the rollout is rolled back, stop routing to new instances and deploy the old notifier version one instance at a time. Its schema remains compatible: it ignores `offer_daily` and continues to read and write `sent`. Queued events remain valid and can be processed by either version.
