# Notifier rollout

## Order

Drain queued `offer.queued` events, then switch customer and notifier together, all instances at once, with no traffic between the old and new versions. The drain avoids replaying work across the boundary; the atomic switch avoids a changed customer consent rule running with an old notifier.

## Mixed versions

The new notifier creates the additive `offer_daily` table and backfills it from existing `sent` rows before accepting traffic. It records accepted and capped offers transactionally in the shared database, while the existing `sent` rows and response shape remain readable. Customer may emit the unchanged `offer.queued {customerId, offerId}` event for either legacy implied or new explicit consent; the atomic boundary means there is no mixed customer/notifier traffic during the rule change.

## Rollback

If either service fails, abort the atomic switch and restore both old versions together; do not leave one new service serving traffic. Do not remove `offer_daily`: the `sent` table remains intact, and retaining the additive counters makes a later retry deterministic. If the new versions had already been switched, roll both back together and preserve the shared database contents.
