# Customer rollout

## Order

No ordering constraint is required between `customer` and `ledger`. The release pipeline may use its default alphabetical, one-instance-at-a-time rollout (`customer` before `ledger`), with no atomic switch and no queue drain.

## Mixed versions

The new customer calls `ledger.balance` for `statement`. It prefers the additive `balanceCents` response field from the new ledger and converts the retained decimal `balance` field when talking to an old ledger. Old customer instances ignore the new response field and continue using payment events. The customer also retains its event-backed balance as a temporary fallback for ledger timeouts or unavailability.

## Rollback

Rollback can stop and replace customer instances independently. Rolling back customer removes `availableCents` from its responses but does not change the shared database or queued events. Rolling back ledger is safe because the customer accepts the old decimal balance response. Do not remove the additive ledger field or alter existing event fields until all new customer instances have been retired.
