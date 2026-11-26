# Customer release

## Rollout order

No cross-service ordering or atomic switch is required. The pipeline may use its default alphabetical, one-instance-at-a-time rollout. Customer can be deployed alongside either the old or new ledger because it accepts both ledger balance response shapes.

## Mixed versions

The new customer returns the additive `availableCents` field and obtains it from `ledger.balance`. It prefers the new integer `balanceCents` field, with a compatibility fallback to the legacy decimal `balance` field. Its existing `balance` and `lines` fields remain backed by the customer event read model. Old customer instances continue serving their existing response and ignore the new field; old and new instances share the unchanged customer schema.

## Rollback

Stop routing traffic to the new customer instances and restore the old version one instance at a time. No database migration or queued-event drain is needed. The old customer can continue consuming existing `payment.posted` events and ignores `availableCents`; if the new ledger is already deployed, customer remains compatible because the new balance response is additive. If ledger is rolled back, the new customer uses its legacy `balance` fallback.
