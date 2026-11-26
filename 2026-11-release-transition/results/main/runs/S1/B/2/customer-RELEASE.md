# Release plan

## Rollout order

1. Deploy the new `customer` version one instance at a time until every customer instance is upgraded and healthy.
2. Only then begin the ledger CHG-101 rollout, also one instance at a time.

The release pipeline should gate the ledger rollout on full customer deployment. No queue drain is required before deploying customer: the new customer can process both event formats.

## Mixed-version behavior

The new customer reads `amountMinor` from new `payment.posted` events and converts it directly to the statement's integer-cent balance. It also accepts the legacy decimal `amount` field for events already queued or delivered by an old ledger. This makes old and new customer instances safe while customer itself is rolling out. The old customer must be fully gone before a new ledger can emit `amountMinor`, because the old customer cannot process that event shape.

## Rollback

If the customer rollout fails, stop it and roll back customer while ledger remains on its old version; queued legacy events remain readable. If ledger has already been upgraded, do not route `amountMinor` events to an old customer: either restore the new customer everywhere first or pause/replay those events after a compatible customer version is restored. A ledger rollback is safe with the new customer because it continues to accept legacy events. Preserve the shared database and event queue during all rollbacks.
