# Ledger release

## Rollout order

1. Deploy the new ledger to all instances, one at a time, and wait for each startup migration to complete.
2. Only after every ledger instance is new, deploy the CHG-103 customer version. The customer rollout must not send `idempotencyKey` while any old ledger instance can receive that traffic.

The ledger release has no atomic-with requirement. The customer release should carry the corresponding `deploy_after: ["ledger"]` constraint in its release plan.

## Mixed-version behavior

Migration 2 only adds a nullable, uniquely indexed column, so old ledger instances continue to read and write the existing columns while new instances use both forms of deduplication. Old customer instances continue sending `requestId` and work unchanged. New customer retries use the same `idempotencyKey` with a new `requestId`; the new ledger returns the original posting and publishes only one event. No new-customer idempotency traffic is allowed until the ledger rollout is complete because old ledger code does not inspect the new field.

## Rollback

If the customer release has started, roll the customer back first, then roll ledger instances back one at a time. The migration and its data remain in the shared database; old ledger code ignores the additive column and resumes `requestId` deduplication. If only ledger needs rollback before customer rollout, it can be rolled back directly. Re-deploying the new ledger later is safe because migration 2 is recorded and existing idempotency keys remain unique.
