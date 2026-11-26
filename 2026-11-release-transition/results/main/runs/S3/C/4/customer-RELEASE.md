# Customer release

## Rollout order

Deploy and verify all ledger instances first. Once ledger is fully upgraded, deploy customer one instance at a time. No atomic switch or event drain is required.

## Mixed-version behavior

The new customer sends the payment reference as `idempotencyKey` on all attempts and uses `requestId` values `<ref>-1`, `<ref>-2`, and `<ref>-3`. It retries only ledger timeouts and returns `FAILED` with `reason=timeout` after the third timeout. The upgraded ledger deduplicates those attempts by the stable idempotency key, so a lost response cannot create a second posting.

The old customer remains usable while ledger rolls out because it sends its legacy `requestId`, which the upgraded ledger continues to honor. Customer rollout starts only after all ledger instances are upgraded, avoiding new customer traffic to the old ledger that cannot interpret the idempotency key.

## Rollback

If customer must be rolled back, restore the old customer instances first; it remains compatible with the upgraded ledger. If ledger must also be rolled back, roll back customer before any ledger instance is reverted, then verify no new customer version is serving. This prevents the new retry protocol from reaching a ledger version that only deduplicates request IDs.
