# Ledger release

## Rollout order

Deploy `customer` completely first, one instance at a time, and wait for all customer instances to run the CHG-101 version. Then deploy `ledger` one instance at a time. No atomic switch or queue drain is required.

## Mixed-version behavior

The ledger `post`, `balance`, and `postings` operations and the postings database schema are unchanged. Old ledger instances publish `payment.posted` with the legacy major-unit `amount`; new ledger instances publish the integer minor-unit `amountMinor` instead. During the customer rollout, the new customer must accept the old event form. After customer is fully deployed, it must accept `amountMinor` from new ledger instances. Queued events keep their original payloads, so consumers must support both forms while old events are in flight.

## Rollback

If the ledger rollout fails, stop it and route traffic back to old ledger instances; they can share the unchanged database and remain idempotent by `requestId`. Old ledger instances will publish legacy `amount` again, so the deployed customer must continue accepting both payload forms. If customer must be rolled back, do so before rolling out new ledger; old customer cannot consume `amountMinor` events.
