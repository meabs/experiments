# Customer release

## Rollout order

There are no service dependencies for this change. The pipeline may use its normal alphabetical, one-instance-at-a-time rollout; ledger does not need to be fully deployed first, and the services do not need an atomic switch.

## Mixed-version behavior

The new customer `statement` operation calls `ledger.balance` and prefers its additive `balanceCents` field. While old ledger instances are serving traffic, customer converts the legacy decimal `balance` field to integer cents. Existing `balance` and `lines` remain backed by customer’s event read model. Old customer instances ignore the additional ledger response field and continue to serve their existing contract.

## Rollback

If customer is rolled back, old customer instances continue using the ledger’s legacy-compatible `balance` response and simply omit `availableCents`; no database migration or event rewrite is required. If ledger is rolled back, the customer fallback continues to work. A failed partial rollout can therefore be retried or rolled back instance by instance without draining events or coordinating an atomic switch.
