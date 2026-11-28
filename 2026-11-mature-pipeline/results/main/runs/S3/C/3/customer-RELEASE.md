# Customer rollout

Deploy `ledger` fully first, one instance at a time. Once every ledger instance is on the CHG-103 version, deploy `customer` one instance at a time. No atomic switch or event drain is required.

During the ledger rollout, old customer instances continue sending the legacy `requestId` field, which the new ledger must continue to accept. After ledger is complete, new customer instances send `idempotencyKey=<ref>` on every attempt and use `<ref>-1`, `<ref>-2`, or `<ref>-3` as the request ID. They retry only timeout responses, so a committed payment whose response was lost is deduplicated by the ledger idempotency key. Old customer instances may run beside new customer instances because both use the compatible ledger contract.

If the customer rollout fails, stop it and route traffic back to old customer instances; their requests remain supported by the upgraded ledger. If rollback occurs after all customer instances were upgraded, the old customer version can still be deployed safely. Do not roll the ledger back to an old version while new customer instances are active, since the old ledger cannot deduplicate the new retry scheme by `idempotencyKey`; roll back customer first, then ledger if necessary.
