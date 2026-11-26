# Notifier rollout

## Order

Switch `customer` and `notifier` atomically, all instances at once, with no traffic between old and new versions. This is required because an old notifier instance does not enforce the new daily cap.

## Mixed versions

The new version creates the additive `offer_daily` table and keeps the existing `sent` table and event contract unchanged. It backfills daily sent counts from existing rows, so `sent` continues to report all historical sends. New instances transactionally claim one of two daily send slots and count later offers as drops; the response adds `capped` while retaining `count` and `ticks`. The unchanged `offer.queued` event remains compatible with the customer version, but the atomic switch prevents old notifier instances from bypassing the cap.

## Rollback

Roll back customer and notifier together to the previous versions. The old notifier ignores `offer_daily` and continues to use `sent`; no destructive migration is needed. If the capped behavior must be restored later, redeploy the new pair, which reuses the retained counters and sent history.
