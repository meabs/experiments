# Ledger rollout

## Order

Deploy ledger one instance at a time using the normal pipeline order. No service must be fully deployed first and no atomic switch is required.

## Mixed versions

The new ledger keeps the existing `post`, `balance`, and `postings` operations and database schema. New `payment.posted` events contain `amountMinor` (minor units as a string) and the deprecated decimal `amount` field. This lets old customer instances continue reading `amount` while CHG-101 customer instances read `amountMinor`. Existing queued events remain consumable by the corresponding customer versions.

## Rollback

If the rollout fails, stop at the failing instance and roll back deployed ledger instances independently. The old ledger can continue using the same postings table and will publish the legacy `amount` field; customer versions that support CHG-101 must retain their compatibility fallback for such events. Do not remove or rewrite existing rows or queued events. Keep the compatibility `amount` field until all old customer instances and legacy events have been retired.
