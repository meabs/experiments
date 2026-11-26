# Ledger rollout

## Order

Deploy and fully switch all `customer` instances first. Only after that rollout has completed, deploy ledger instances one at a time. No event drain is required: queued events are deliberately handled by both customer versions.

## Mixed-version behavior

The old ledger publishes `payment.posted.amount`; the new ledger publishes `payment.posted.amountMinor` and retires `amount`. Therefore an old customer instance must not receive events from a new ledger instance. During the customer rollout, the new customer reader must accept both fields, allowing it to consume queued old-ledger events. Once customer is fully deployed, new ledger instances may publish `amountMinor`.

The ledger database schema and posting operations are unchanged, so old and new ledger instances can share the existing database during a one-at-a-time rollout. Existing queued events are also preserved.

## Rollback

If the ledger rollout fails, switch ledger instances back to the old version. The new customer reader can consume the old ledger's legacy `amount` events, so this rollback is safe. If customer must be rolled back after ledger has switched, roll ledger back first (or leave the new customer reader deployed); do not expose new-ledger events to an old customer reader.
