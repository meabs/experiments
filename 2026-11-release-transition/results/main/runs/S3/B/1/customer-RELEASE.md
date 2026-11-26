# Customer release

## Rollout order

1. Deploy the ledger idempotency-key release to every ledger instance and confirm it is fully deployed.
2. Deploy customer one instance at a time, checking payment success and duplicate-post metrics between instances.

The `deploy_after` constraint in `plan.json` enforces the ledger-before-customer dependency. No queue drain or all-at-once switch is required.

## Mixed-version behavior

The new customer sends `idempotencyKey=<ref>` on every ledger call and uses `requestId=<ref>-<attempt>`, retrying timeout responses at most three times. The new ledger deduplicates retries by the idempotency key, so old and new customer instances can safely share it during the customer rollout. The old customer remains compatible with the new ledger because it still sends `requestId=<ref>`, which the ledger must continue to support.

Do not run the new customer against an old ledger: the old ledger ignores `idempotencyKey` and would see the fresh retry request IDs as distinct postings.

## Rollback

If the customer rollout fails, stop it and roll customer instances back; the new ledger can continue serving old customer instances through its legacy `requestId` behavior. If the ledger must be rolled back, first roll every customer instance back to the old version, then roll back ledger. A payment receiving three timeout responses returns `FAILED` with `reason=timeout`; non-timeout ledger errors are returned unchanged.
