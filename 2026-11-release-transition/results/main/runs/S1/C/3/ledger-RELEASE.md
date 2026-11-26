# Ledger rollout

## Rollout order

Ledger has no hard deployment constraint. It may be rolled out one instance at a time alongside the customer rollout. For the simplest operational transition, deploy ledger first and then customer, allowing the customer consumer to observe both event shapes during the overlap.

## Mixed versions

The ledger database schema and the `post`, `balance`, and `postings` operations are unchanged. New ledger instances publish `payment.posted` with the required `amountMinor` string and also retain the deprecated decimal `amount` field. Therefore old customer instances continue to consume new events, while updated customer instances can use minor units. Events already queued before deployment remain readable by the corresponding compatibility logic.

## Rollback

If the rollout fails, stop new ledger instances and route traffic back to the old ones. The shared schema is unchanged, and old ledger instances ignore the additive event field, so they can operate on the same database. Keep the compatibility fields until all queued events and old customer instances are gone; this makes a customer or ledger rollback safe without rewriting stored postings or events.
