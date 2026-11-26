# Notifier rollout

## Order

Deploy notifier independently; there is no required ordering relative to customer because `offer.queued {customerId, offerId}` is unchanged by CHG-104. The service may therefore follow the pipeline's normal alphabetical, one-instance-at-a-time rollout. No queue drain or atomic switch is required.

## Mixed versions

The new version creates the additive `offer_caps` table and keeps reading the existing `sent` table, so it can process events produced by either customer version and can start against an existing database. New notifier instances serialize daily-cap decisions through the shared table and count pre-existing sent rows for the current platform day. The old notifier ignores `offer_caps`; while it is still serving traffic, offers handled by it are not capped. The new contract is fully effective after the last old notifier instance is removed.

## Rollback

Stop or replace new instances with the previous notifier version and leave both tables in place. Existing sent rows remain valid, and the old version ignores the additive `offer_caps` table. A rollback restores delivery behavior but does not enforce the daily cap, so re-deploy the new version to regain cap enforcement; do not delete or reset `offer_caps`, since that would lose the cumulative `capped` counts.
