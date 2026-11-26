# Customer release

## Rollout order

Deploy customer one instance at a time in the pipeline's default alphabetical order; there is no dependency on ledger deployment and no need for an atomic switch or event drain.

## Mixed-version behavior

The new customer calls `ledger.balance` when serving `statement` and returns its `balanceCents` field as `availableCents`. During the transition it also accepts the old ledger response's decimal `balance` and converts it to integer minor units. Old customer instances continue to work with either ledger version because they ignore the additional response field from a new ledger and continue using their event read model.

The existing `balance` and `lines` fields remain unchanged and continue to be built from retained `payment.posted` events. The new synchronous balance lookup does not alter events or either service's database.

## Rollback

If the rollout is rolled back, route traffic back to old customer instances one at a time. They remain compatible with both ledger versions, and no database or queued-event rollback is required. A later retry of the customer rollout can safely read the same retained events and ledger balance.
