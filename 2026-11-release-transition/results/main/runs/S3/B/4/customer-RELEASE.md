# Customer CHG-103 rollout

## Order

Deploy ledger completely first, one instance at a time. Once all ledger instances support the additive `idempotencyKey` request field, deploy customer one instance at a time. No queue drain or atomic switch is required.

## Mixed versions

The new customer sends the existing `account`, `amount`, and `requestId` fields plus `idempotencyKey`; this is additive for ledger. It retries only timed-out calls, using the payment reference as the stable idempotency key and `<ref>-1`, `<ref>-2`, and `<ref>-3` as distinct tracing request IDs. Therefore a new customer can safely call any new ledger instance, and an old customer remains compatible with new ledger because it still supplies `requestId`.

## Rollback

If the customer rollout fails, stop it and route traffic back to old customer instances; new ledger can remain deployed because the old request shape remains supported. If ledger must be rolled back, first roll customer back completely and stop new customer instances, then roll ledger back. Do not leave new customer instances serving against old ledger: an old ledger does not understand the idempotency key and cannot guarantee deduplication when a timeout follows a committed post.
