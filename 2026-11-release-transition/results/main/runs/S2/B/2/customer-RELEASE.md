# Customer and ledger rollout

## Rollout order

There is no customer-specific ordering constraint. Use the pipeline's default order (one instance at a time; alphabetically, `customer` before `ledger`), or roll either service first. Keep the ledger's existing `balance` response field while adding `balanceCents`.

## Mixed-version behavior

New customer instances call `ledger.balance` for `statement`. They use `balanceCents` when returned by a new ledger and convert the legacy two-decimal `balance` response when talking to an old ledger. The statement's event-derived `balance` and `lines` remain unchanged, and `availableCents` is added to the response. Old customer instances ignore the additive ledger response field and continue consuming the unchanged `payment.posted` event.

The database and queued events need no migration or drain: the event shape is unchanged and the customer read model remains valid across versions.

## Rollback

If the customer rollout fails, stop it and route traffic back to old customer instances; they remain compatible with both ledger response shapes. If the ledger rollout fails, stop it and restore old ledger instances while retaining the legacy `balance` field; new customer instances will use their fallback conversion. Because the changes are additive and no traffic switch must be atomic, either service can be rolled back independently, with no database or event rollback required.
