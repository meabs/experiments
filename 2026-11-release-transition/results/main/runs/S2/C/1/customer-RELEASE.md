# Customer release

## Rollout order

No ordering constraint is required. The pipeline may use its default alphabetical, one-instance-at-a-time rollout. Customer can be deployed independently of ledger; no queue drain or atomic switch is required.

## Mixed-version behavior

New customer instances call `ledger.balance` for `statement`. They use `balanceCents` when the new ledger supplies it, and convert the legacy decimal `balance` when an old ledger instance responds. The response continues to include the existing local `balance` and `lines` fields and adds `availableCents`.

The customer consumer accepts the existing decimal `payment.posted.amount`; it also accepts an additive `amountCents` field if the new ledger publishes one. Ledger must retain the legacy `balance` response field and decimal event amount while old customer instances remain active. Old customer instances ignore the new customer response field and continue using their local event read model.

## Rollback

Rollback can switch customer instances back one at a time without changing the database or draining events. The old customer ignores `availableCents` and remains compatible with the retained ledger response/event fields. If ledger is rolled back first, new customer instances use the decimal fallback. If customer is rolled back first, the old customer remains compatible with the additive ledger fields.
