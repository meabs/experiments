# Notifier rollout

## Order

First drain the `offer.queued` queue completely. Then deploy the customer and
notifier as one atomic change: all instances switch together, with no traffic
between the old and new pair. The drain is required because the queue is
persistent and an old customer can have left offers in it.

## Mixed-version behaviour

There is no supported mixed-traffic window for this release. Before the
cutover, the old customer/notifier pair continues to process its existing
events. After the cutover, the new pair consumes the same event shape and
stores the daily-cap state in the additive `offer_day` table. Existing `sent`
rows remain authoritative, so an instance restart or a replay cannot reset
the two-per-customer-per-day limit.

## Rollback

If any instance fails, stop the atomic rollout and switch every customer and
notifier instance back to the previous versions together. Do not roll back
only one service and do not resume traffic until the pair is restored. Since
the queue was drained before cutover and the database is shared, this avoids
an old notifier processing an event after the new customer marketing rule.
