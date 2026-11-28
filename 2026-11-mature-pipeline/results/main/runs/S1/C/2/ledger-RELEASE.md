# Ledger release (CHG-101)

## Rollout order

1. Deploy the customer CHG-101 release to all customer instances and wait until the old customer version has been fully replaced.
2. Deploy ledger one instance at a time.

The `deploy_after` constraint in `plan.json` enforces the first step. No event drain is required: the customer reader must accept both the legacy `amount` event and the new `amountMinor` event while queued events are being delivered.

## Mixed-version behavior

Ledger keeps its existing decimal `post`, `balance`, and `postings` interface and database representation. The new ledger publishes `payment.posted` with `account`, `amountMinor` (minor units as a string), and `requestId`; it does not publish the retired `amount` field.

Because customer is fully upgraded first, an old customer instance cannot consume a new ledger event. During the customer-first rollout, old ledger events remain readable by the new customer, including events that were already queued before deployment.

## Rollback

If the ledger rollout fails, stop it and restore the previous ledger version one instance at a time. The upgraded customer continues to accept the old ledger's `amount` events, so rollback does not require reverting customer or changing the shared database. Existing postings and queued events are retained and processed normally.
