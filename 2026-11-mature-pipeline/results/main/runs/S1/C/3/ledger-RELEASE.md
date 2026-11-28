# Ledger rollout

## Order

With no cross-service constraint, the pipeline order is customer, decision, ledger, notifier; deploy ledger one instance at a time in its alphabetical slot. No service needs to be fully deployed first, and ledger does not need an atomic switch or an event drain.

## Mixed versions

The new ledger publishes `amountMinor` as the canonical minor-unit string and also keeps publishing the deprecated decimal `amount`. Old customer instances continue to read `amount`; new customer instances read `amountMinor`. Existing postings and the database schema are unchanged, so old and new ledger instances can share the database.

## Rollback

Stop the affected new ledger instance and route traffic back to the old version. The old version can continue reading and writing the unchanged postings table, and its decimal event is still present on events emitted by the new version. Queued events remain consumable by either customer version. Retire the compatibility `amount` field only in a later release after all old customer versions and rollback targets are gone.
