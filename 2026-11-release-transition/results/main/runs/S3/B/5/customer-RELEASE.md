# Customer CHG-103 rollout

## Rollout order

Deploy the new ledger to every instance first, allowing its compatibility rollout to complete. Then deploy customer one instance at a time. No queue drain or atomic switch is required.

## Mixed-version behaviour

The new customer sends `idempotencyKey=<ref>` on every ledger attempt and uses request IDs `<ref>-1`, `<ref>-2`, and `<ref>-3`. It retries only timeout responses, up to three total attempts. The new ledger accepts these additive fields and deduplicates retries by the stable idempotency key. During the customer rollout, old customer instances continue to send their legacy `requestId=<ref>` calls; the new ledger continues to support that field and its existing deduplication behaviour.

## Rollback

If the customer rollout is rolled back, stop new customer deployments and replace upgraded instances with the previous customer version. Leave the upgraded ledger in place: it remains backward compatible with the old customer's request format. Do not roll back ledger independently to an older version after new customer instances have been deployed unless customer is rolled back first; otherwise retries could lose the idempotency-key guarantee.
