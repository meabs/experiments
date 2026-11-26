# Release plan

## Rollout order

1. Drain all queued `payment.posted` events while the current ledger and customer versions are serving.
2. Switch every ledger and customer instance atomically, with no traffic between the two versions. The release constraint is `atomic_with: ["customer"]`.

There is no one-service-at-a-time rollout for this contract change: `payment.posted` now requires the `amountMinor` string and no longer carries the decimal `amount` field.

## Mixed-version behaviour

The new and old contract versions must not receive traffic together. Draining first ensures old customer instances have consumed all old-format events before the cutover, and the atomic switch ensures new customer instances only receive new-format events from new ledger instances. The ledger database schema is unchanged, so existing postings and idempotency records remain usable by either ledger version.

## Rollback

If the release fails, stop new traffic and drain all events produced by the new pair. Then atomically switch ledger and customer back to their previous versions; never roll back just one service. Existing database rows are retained, and the queue must be empty before the rollback so the old customer cannot encounter a new-format event. Re-run the drain and switch procedure before retrying the release.
