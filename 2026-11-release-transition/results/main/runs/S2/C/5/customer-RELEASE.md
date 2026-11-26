# Customer release

## Rollout order

Deploy customer independently, one instance at a time. It does not need to wait for ledger, be switched atomically with ledger, or drain queued events first. The normal pipeline order is therefore safe, including an order where old and new ledger instances coexist.

## Mixed-version behaviour

For `statement`, the new customer calls `ledger.balance` and returns its `balanceCents` value as `availableCents`. While old ledger instances are still serving traffic, they return the legacy decimal `balance`; customer converts that value exactly to integer cents. New ledger instances may return both fields, and customer prefers `balanceCents`. The existing event-built `balance` and `lines` fields remain unchanged, so queued `payment.posted` events can be processed before or after the rollout.

## Rollback

Rollback customer one instance at a time. Old customer instances continue returning the original `balance` and `lines` fields and do not depend on `availableCents`; the shared database schema is unchanged. Ledger can also be rolled back independently because the customer accepts its legacy decimal balance response. Any queued events remain valid and can be consumed by either customer version.
