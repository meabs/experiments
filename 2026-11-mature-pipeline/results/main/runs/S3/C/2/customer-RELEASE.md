# Customer release

## Rollout order

Deploy all ledger instances with CHG-103 first. Once ledger is fully deployed and healthy, deploy customer one instance at a time. No event-queue drain is required before customer deployment.

## Mixed-version behavior

During the ledger rollout, old customer instances continue sending the existing `requestId=ref` request and remain compatible with both old and new ledger instances. Customer rollout starts only after all ledger instances support `idempotencyKey`. New customer instances send the same `idempotencyKey=ref` on every attempt and a distinct `requestId=<ref>-<attempt>`; ledger therefore posts a payment once even when an attempt times out. Old and new customer instances can coexist after that point, and the shared ledger idempotency data and queued events are retained.

## Rollback

If the customer rollout fails, stop it and roll customer instances back to the previous version. The previous customer uses `requestId=ref`, which remains supported by the new ledger, so rollback does not require reversing ledger data or draining events. If ledger must also be rolled back, roll customer back first and then follow ledger's rollback procedure; do not run the new customer against any old ledger instance.
