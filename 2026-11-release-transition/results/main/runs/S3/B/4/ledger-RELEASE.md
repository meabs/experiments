# Ledger rollout

Deploy ledger one instance at a time in the normal pipeline order. No service needs to be fully deployed first, and no atomic switch or queue drain is required.

At startup, the new version migrates schema version 1 to version 2 by adding a nullable `idempotency_key` and replacing the old `request_id` uniqueness constraint with a unique nullable index on the new key. Existing rows and queued events are unchanged. During a mixed rollout, old instances continue to deduplicate by `requestId`; new instances do the same when no idempotency key is supplied, and use `idempotencyKey` when it is supplied. The request ID in the published event remains the original trace ID, and extra request fields do not affect old callers.

If rollout fails, stop deploying and route traffic back to old instances. They can use the migrated table because the added column is nullable and their inserts omit it. Existing keyed postings remain durable; old instances may only apply their legacy request-ID semantics to subsequent calls. After the issue is corrected, resume the rollout. Do not roll back by deleting or reverting the schema migration.
