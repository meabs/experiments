# Customer release

## Rollout order

Deploy the new `ledger` to all instances first, then roll out the new `customer` one instance at a time. No queue drain is required: this change only affects synchronous payment calls, and queued `payment.posted` events remain compatible.

## Mixed-version behavior

The new customer sends the payment `ref` as `idempotencyKey` on every ledger attempt and uses `ref-1`, `ref-2`, or `ref-3` as the tracing `requestId`. It retries only `timeout`, for at most three total attempts. The new ledger must continue accepting old customer requests that provide only `requestId=ref`, while deduplicating the new attempts by `idempotencyKey`; therefore a payment is posted once when old and new instances overlap.

During the ledger-first phase, old customer instances continue using their legacy request IDs and remain supported by the new ledger. During the customer rollout, either customer version can call any ledger instance.

## Rollback

If the customer rollout fails, stop it and route traffic back to the old customer version. Keep the upgraded ledger deployed: it supports the old request shape, so rollback needs no database or event cleanup. If the ledger rollout itself must be rolled back before customer rollout starts, roll back the ledger first and do not deploy the new customer until the ledger upgrade is restored; otherwise the new customer's attempt-specific request IDs could be treated as separate legacy posts.
