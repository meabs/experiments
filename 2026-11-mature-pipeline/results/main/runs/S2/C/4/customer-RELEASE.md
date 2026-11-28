# Customer release

## Rollout order

Customer has no deployment ordering, atomicity, or event-drain constraint. It may roll out one instance at a time under the normal alphabetical pipeline order. It is safe to deploy before, during, or after the ledger integer-amount rollout.

## Mixed-version behavior

New customer instances call `ledger.balance` and use `balanceCents` when present. They fall back to converting the legacy decimal `balance` field to cents, so they work with old and new ledger instances. Old customer instances ignore the additive `balanceCents` field and continue using payment events for their existing statements. The customer still reports its event read-model `balance` and `lines`; only `availableCents` is sourced from the current ledger balance.

The ledger rollout must preserve the legacy `balance` response field until old customer instances are gone. No event schema or customer database migration is required.

## Rollback

If the rollout fails, stop and roll back customer instances individually to the previous version. The shared customer database and queued `payment.posted` events remain usable because this change adds no schema or event-format dependency. Keep the ledger's legacy `balance` field during any ledger rollback or mixed-version period; customer can then continue serving statements. A later retry can redeploy the new customer version without replaying or rewriting existing events.
