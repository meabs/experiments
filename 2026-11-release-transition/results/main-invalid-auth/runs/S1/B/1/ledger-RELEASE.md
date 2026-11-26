# Ledger release

## Rollout order

Deploy and complete the customer CHG-101 rollout first. Confirm that all customer instances consume both legacy `payment.posted.amount` events and the new `payment.posted.amountMinor` events. Then deploy ledger one instance at a time. No event drain is required, because the customer handles both event formats while the rollout is in progress.

## Mixed-version behavior

The ledger database schema and the `post`, `balance`, and `postings` operations are unchanged. Old ledger instances publish the legacy decimal `amount`; new ledger instances publish only the integer-string `amountMinor`. During the ledger rollout, the new customer consumes either format, and queued events retain their original format. The new ledger can therefore run beside old ledger instances without changing persisted data or losing events.

## Rollback

Stop the new ledger instances and restore the previous ledger version one instance at a time. The restored instances publish legacy `amount` events, which the already-upgraded customer continues to accept. Do not roll back customer before ledger has been restored (or otherwise ensure the customer can still consume `amountMinor` events); queued events and the shared postings database are retained across the rollback.
