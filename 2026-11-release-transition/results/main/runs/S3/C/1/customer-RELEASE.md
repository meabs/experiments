# Customer release

## Rollout order

Wait for the ledger CHG-103 rollout to complete on all instances, then deploy customer one instance at a time. No queue drain is required: the `payment.posted` event shape is unchanged and existing queued events remain valid.

## Mixed-version behavior

The new customer sends the existing `account`, `amount`, and `requestId` fields plus `idempotencyKey=ref`. On a timeout it retries up to three total attempts, using `ref-1`, `ref-2`, and `ref-3` as request IDs. The stable idempotency key lets the new ledger post a payment once even if an earlier response was lost. A new customer instance must not be exposed to an old ledger instance, so the ledger deployment is a prerequisite.

Old customer instances continue to send their legacy single request with `requestId=ref`; the new ledger remains backward-compatible with that request. Thus old and new customer instances can coexist while the customer rollout proceeds.

## Rollback

If customer is rolled back, keep the new ledger deployed: old customer requests remain supported and use the ledger's legacy `requestId` idempotency. If ledger itself must be rolled back, first roll customer back to the old version (and stop routing to new customer instances), then roll ledger back. Do not run new customer instances against an old ledger, since fresh retry request IDs would not provide exactly-once behavior there.
