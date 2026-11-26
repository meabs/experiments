# Customer CHG-103 rollout

## Order

1. Fully deploy the ledger CHG-103 version to all instances and verify its health and idempotent-post behavior.
2. Deploy the customer version one instance at a time. The release constraint in `plan.json` prevents this customer rollout from starting before ledger is complete.

With this constraint, there is no period in which the new customer sends idempotency keys to the old ledger. The old customer can run alongside the new ledger during the ledger rollout: it continues sending its legacy `requestId=ref`, which the new ledger accepts as the backward-compatible fallback.

## Mixed versions

The new customer sends the same `idempotencyKey=ref` on all three possible attempts and a distinct `requestId` (`<ref>-1`, `<ref>-2`, `<ref>-3`) on each attempt. A timeout is retried; success returns `OK`; three timeouts return `FAILED` with `reason=timeout`. The ledger deduplicates retries by the stable idempotency key, so a lost response cannot create multiple postings.

## Rollback

If the customer rollout fails, stop it and route traffic back to the old customer version. The old customer remains compatible with the new ledger. If the ledger itself must be rolled back, first roll the customer back to the old version and confirm no new customer instances are serving; then roll ledger instances back one at a time. Preserve the database and queued events throughout, and do not deploy the new customer against the old ledger.
