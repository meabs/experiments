# Notifier rollout

## Order

Deploy notifier one instance at a time. It may be rolled out before or after customer; no `deploy_after`, `atomic_with`, or queue drain constraint is needed because the published `offer.queued {customerId, offerId}` event is unchanged.

## Mixed versions

The new version creates the additive `offer_dropped` and `offer_cap_lock` tables on startup and continues to use the existing `sent` table. It counts existing `sent` rows for the current platform day, sends only the first two offers for a customer in that day, and cumulatively records later offers as dropped. The per-customer lock serializes overlapping new instances. The `sent` response gains the additive `capped` field; old callers can ignore it. Old notifier instances can read and write the unchanged `sent` schema while the new version is present.

## Rollback

Stop or replace new instances with the previous version. The previous version ignores the additive table and continues processing the unchanged event and `sent` schema; no migration rollback or data deletion is required. Retain `offer_dropped` so a later redeployment of the new version preserves the cumulative count. During a rollback, the old implementation does not enforce the new cap, so re-enable the new version when cap enforcement is required.
