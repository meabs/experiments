# Customer CHG-103 rollout

## Rollout order

Deploy the ledger change first and wait until all ledger instances are on the new version. Then deploy customer one instance at a time. No queue drain or atomic switch is required.

## Mixed-version behavior

The new customer sends `idempotencyKey=<ref>` on every ledger post and uses `requestId=<ref>-<attempt>` for attempts 1–3. It retries only timeout responses, so the upgraded ledger deduplicates a payment even if an earlier attempt committed before its response was lost. During the customer rollout, old customer instances continue sending their legacy `requestId=<ref>` requests; the new ledger must continue accepting those requests and preserving request-ID idempotency. Events remain unchanged.

## Rollback

If the customer rollout fails, stop it and route traffic back to the old customer version. Keep the upgraded ledger deployed: it must remain backward compatible with the old customer contract and retain its idempotency data. Do not roll back ledger independently while any new customer instance might retry with `idempotencyKey`; if ledger rollback is required, first remove the new customer instances and confirm no new-version traffic remains.
