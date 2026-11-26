# Ledger rollout

Deploy the ledger instances one at a time, completing ledger before deploying the customer change that sends `idempotencyKey`. No atomic switch is required. The startup migration upgrades schema version 1 to 2 by adding a nullable column and a unique index, so the shared database remains readable by both versions.

While old and new ledger instances coexist, old callers continue to use `requestId` exactly as before. New ledger instances accept both forms: requests without a key retain request-ID idempotency, while keyed requests deduplicate on `idempotencyKey` and publish the optional field in `payment.posted`. Existing consumers can ignore that additive event field, and new customer instances must only send keys once all ledger instances support them.

If rollout fails, stop new traffic to the failed instance and roll back to the previous ledger version. The migration is forward-compatible: the old version ignores the nullable column and continues using `requestId`; retain the migrated database and queued events. Before retrying the customer rollout, ensure all ledger instances are new again. If the customer rollout is already active, stop keyed retries or complete ledger deployment before rollback; otherwise a rolled-back ledger cannot guarantee keyed deduplication.
