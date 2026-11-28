# Customer release: CHG-101

## Rollout order

1. Deploy the new customer version one instance at a time until every customer
   instance is running it.
2. Only after that, deploy the ledger version that publishes `amountMinor`.
   The ledger team's release plan must enforce this customer-before-ledger
   dependency.

No queue drain is required before deploying customer: the new consumer accepts
both event formats.

## Mixed-version behavior

The new customer reads `amountMinor` and converts it directly to the persisted
minor-unit balance. It falls back to legacy `amount` for events emitted by an
old ledger or already present in the queue. Therefore old and new customer
instances can coexist while the old ledger is running. Once ledger starts
publishing `amountMinor`-only events, an old customer must not receive traffic;
the customer rollout must already be complete.

## Rollback

If customer deployment fails before ledger changes, roll back customer
instances one at a time; the old customer continues to consume legacy ledger
events. If ledger has been switched, do not roll back customer to the old
version independently, because it cannot read `amountMinor`; roll back ledger
first (or keep this compatible customer version deployed), then roll back
customer. Persistent statement balances and queued events are retained, and
the compatible customer can process either event format after recovery.
