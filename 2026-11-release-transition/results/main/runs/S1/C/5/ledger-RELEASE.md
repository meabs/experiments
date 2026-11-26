# Ledger rollout

## Order

Deploy ledger one instance at a time using the normal alphabetical pipeline order. No `deploy_after` or `atomic_with` constraint is needed for this release. The ledger database migration is unchanged, so all instances continue to use the existing `postings` table.

## Mixed versions

The new ledger accepts the existing `post` request and keeps the existing `balance` and `postings` responses. Its `payment.posted` events add the string field `amountMinor` while retaining the legacy decimal `amount` field. Therefore old customer instances can consume events from new ledger instances, and new customer instances can consume events produced by either ledger version (using `amountMinor` for the new read model). Existing queued events remain readable through the legacy field.

## Rollback

If rollout fails, stop at the last healthy instance and route traffic back to the old ledger version. The shared schema is unchanged, and events written by the new version remain compatible with the old customer and ledger versions. Retry or roll back without deleting postings or queued events; idempotency by `requestId` remains unchanged.

The legacy `amount` field must not be removed until the customer migration is complete and queued events have drained. That removal belongs in a later coordinated release.
