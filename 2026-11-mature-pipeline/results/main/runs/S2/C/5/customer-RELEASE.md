# Customer release

## Rollout order

Use the normal one-instance-at-a-time pipeline order. With no cross-service
constraint, that order is alphabetical, so `customer` rolls out before
`ledger`. No instances need to be switched atomically and queued events do not
need to be drained first.

## Mixed versions

The new customer calls `ledger.balance` for `statement`. It uses the additive
`balanceCents` response when a new ledger is serving the request and converts
the existing decimal `balance` response when an old ledger is serving it.
Therefore old and new ledger instances can serve requests together. Old
customer instances do not call this field and continue to work with either
ledger version. Existing `payment.posted` events remain decimal and are still
consumed by customer, so queued events are compatible across the rollout.

## Rollback

If the rollout is stopped or rolled back, route traffic back to the old
customer instances. They remain compatible with both ledger versions, and the
shared customer read model and queued events require no rollback migration.
The new ledger may likewise be rolled back independently because the customer
keeps the legacy `balance` fallback and does not require `balanceCents`.
