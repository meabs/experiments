# Ledger rollout

Deploy the new ledger instances one at a time, keeping the old instances serving traffic. Complete the ledger rollout before starting customer CHG-103, so every ledger instance that can receive a keyed retry understands `idempotencyKey`.

The startup migration adds a nullable, unique `idempotency_key` column and removes only the old database uniqueness constraint on `request_id`. Old ledger binaries ignore the extra column and continue to read and write legacy rows. New binaries deduplicate keyed calls by `idempotencyKey`, while requests without a key retain requestId-based behavior. A keyed retry with a new requestId returns the original id and publishes no second event.

If the rollout is rolled back, stop routing new keyed customer traffic to the old ledger version (pause or roll back the customer rollout first). The schema change is forward-compatible: old binaries can run against it, and existing rows remain valid. Legacy requestId-only traffic continues to work during and after rollback; keyed retries should wait for the new ledger version to be restored.
