# Ledger release

## Rollout order

1. Deploy the customer change to all instances, one instance at a time, and wait until it is fully deployed.
2. Deploy the ledger change one instance at a time.

The customer change must be able to read both the legacy `payment.posted.amount` field and the new `payment.posted.amountMinor` field before ledger rollout begins. No queue drain is required: queued events remain durable and are processed after each instance starts.

## Mixed-version behavior

While customer instances are mixed, old ledger instances continue publishing the legacy decimal `amount`, which the new customer reader accepts. Once ledger rollout starts, new ledger instances publish `amountMinor` only; the already-deployed customer version accepts that form. Ledger's synchronous `post`, `balance`, and `postings` operations and its existing database remain unchanged. Replayed events retain their original payload shape.

## Rollback

If ledger rollout fails, stop the rollout and restore the previous ledger version. The old ledger publishes the legacy `amount` field, so the new customer reader must continue accepting that field while rollback is in progress. Do not delete or rewrite queued events or database rows; process them with the compatible reader. If the customer rollout itself fails, finish or roll back customer before changing ledger, and keep ledger on its old version until customer again supports both event formats.
