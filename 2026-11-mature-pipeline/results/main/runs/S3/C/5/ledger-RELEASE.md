# Ledger release

## Rollout order

1. Roll out the new ledger one instance at a time until every ledger instance is running the new version.
2. Roll out the customer CHG-103 version only after ledger is fully deployed. No queue drain is required for ledger.

The customer release should express `deploy_after: ["ledger"]`; this service does not require an atomic switch with customer.

## Mixed-version behavior

The schema migration is additive: version 2 adds a nullable `idempotency_key` column and a unique index. Old ledger instances ignore both and continue using `request_id`; new instances continue to support those requests exactly as before. New ledger instances use `idempotencyKey` when present, return the original posting for retries with `dup=true`, and publish only the first event. `requestId` remains the per-call trace ID in the event.

During the ledger rollout, old customer instances remain compatible because they send no idempotency key. The new customer must wait until the rollout is complete: old ledger instances cannot deduplicate a stable idempotency key when retry request IDs differ.

## Rollback

If ledger validation fails, stop the rollout and restore old ledger instances. The extra nullable column, index, and schema version can remain in the shared database; old binaries ignore them. If customer CHG-103 has already started, roll it back or stop its traffic before using old ledger instances, since the old ledger does not honor `idempotencyKey`. Once ledger is healthy again, resume the customer rollout.
