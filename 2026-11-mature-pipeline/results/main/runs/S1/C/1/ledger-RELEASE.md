# Ledger release

## Rollout order

Deploy ledger one instance at a time using the normal pipeline order. No service dependency or atomic switch is required for this release: every ledger version publishes both the new `amountMinor` field and the legacy `amount` field.

## Mixed-version behavior

The posting API, stored postings, idempotency behavior, and balance operations are unchanged. New ledger instances publish `payment.posted.amountMinor` as an integer pence string and continue publishing `amount` as a deprecated decimal compatibility field. This lets old customer instances consume events through `amount`, while the CHG-101 customer version consumes `amountMinor`; events already queued remain readable by either version.

## Rollback

If the rollout is rolled back, route traffic back to the old ledger instances. The old ledger can continue serving the unchanged posting API and its events retain `amount`, so old customer instances remain compatible. Do not remove the compatibility `amount` field until all old customer consumers and any queued-event processing paths have been retired; removing it is a separate coordinated release.
