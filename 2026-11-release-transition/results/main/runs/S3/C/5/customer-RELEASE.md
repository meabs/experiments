# Customer release

## Rollout order

Deploy and fully roll out `ledger` first, including its idempotency-key support. Then deploy `customer` one instance at a time. No atomic switch or event-queue drain is required.

## Mixed-version behavior

The new customer sends the payment reference as the stable `idempotencyKey` on every ledger attempt and uses `<ref>-<attempt>` as the per-attempt `requestId`. It retries timeout responses up to three total attempts. A new ledger deduplicates those attempts by idempotency key, so a lost response cannot create a second posting. Old customer instances continue sending `requestId=ref`; the new ledger must continue accepting and deduplicating that legacy form while mixed versions run.

## Rollback

If customer is rolled back, old customer remains compatible with the new ledger because the legacy request ID is still supported. If ledger must be rolled back after the new customer is deployed, first roll customer back (or stop routing payments to the new customer), because an old ledger would not recognize `idempotencyKey` and could post each retry's fresh request ID separately. Existing postings, events, and idempotency records are retained throughout rollback.
