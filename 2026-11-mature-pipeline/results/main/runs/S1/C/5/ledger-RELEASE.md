# Ledger release

## Rollout order

Drain queued `payment.posted` events, then switch `ledger` and `customer` as one atomic deployment group. There must be no traffic interval in which a new ledger can publish to only old customer instances. The services can otherwise be deployed one instance at a time; the atomic constraint applies to the version switch for both services.

## Mixed-version behavior

The new ledger keeps the existing `post`, `balance`, and `postings` operations and database unchanged. New payment events contain the required `amountMinor` integer string and retain the old decimal `amount` key as a deprecated compatibility alias. Consequently, old customer instances can consume events published by new ledger instances, while the new customer read model can use `amountMinor` and still consume events already queued by old ledger instances.

The alias is intentionally temporary. It must not be removed until no old customer/ledger instances remain and the event queue has been drained; that removal belongs in a later coordinated release.

## Rollback

If either service fails, stop the atomic group and roll both services back together. Do not roll back only one service. Events and the shared database remain valid: old customer can consume new-ledger events because the compatibility `amount` key is present, and new customer can consume old-ledger events using its legacy-format fallback. Drain the queue after the rollback before resuming normal traffic. If the alias has already been removed in a future release, restore that compatible version before rolling back.
