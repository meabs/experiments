# Customer release

## Rollout order

Deploy the ledger CHG-103 release completely before deploying customer. Once every ledger instance is new, roll out customer one instance at a time. No event drain or atomic switch is required.

## Mixed-version behavior

The new customer calls `ledger.post` with the existing `account`, `amount`, and `requestId` fields, plus the additive `idempotencyKey`. It retries timeouts at most three times, using the payment reference as the stable idempotency key and `<ref>-<attempt>` as the per-attempt request ID. The new ledger deduplicates those attempts as one payment. During the customer rollout, old customer instances continue their single legacy call and remain supported by the new ledger.

The ledger must be fully upgraded first because an old ledger only deduplicates `requestId`; receiving the new customer’s distinct retry request IDs could otherwise create duplicate postings after a lost response.

## Rollback

Roll back customer independently, one instance at a time, to the previous customer version. The old customer sends the legacy `requestId=ref`, which remains supported by the new ledger. Do not roll the ledger back to its old version while any new customer instance is active; first complete the customer rollback. Existing postings and queued events are retained across either rollback.
