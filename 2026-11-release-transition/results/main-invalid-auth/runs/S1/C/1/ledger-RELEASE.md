# Ledger CHG-101 release

## Rollout order

Deploy ledger one instance at a time using the normal pipeline order. No service must be fully deployed first, no atomic switch is needed, and queued events do not need to be drained before deployment.

## Mixed versions

The new ledger publishes `payment.posted.amountMinor` as the canonical integer number of pence, and also continues publishing the legacy decimal `amount`. Old and new ledger instances share the existing database and produce the same event shape. Old customer instances continue reading `amount`; new customer instances read `amountMinor`, so either customer version can process events produced by either ledger version. Existing queued events remain consumable by the old customer and are not rewritten.

The legacy `amount` field is a compatibility bridge, not a field to remove in this rollout. Its removal requires a later coordinated compatibility check after old customer instances and queued events are gone.

## Rollback

If the rollout fails, stop and route traffic back to the old ledger instances. They continue to read the unchanged `postings` schema and publish the legacy `amount` field, so old and new customer versions remain compatible. The new ledger does not require a schema migration; postings and queued events remain intact. If new-ledger events are already queued, old customer instances can still consume them because `amount` is retained.
