# Customer release

## Rollout order

Deploy customer instances one at a time in the normal pipeline order. No ledger ordering, atomic switch, or queue drain is required: this version interoperates with both the old and CHG-102 ledger versions.

## Mixed-version behavior

`statement` continues to derive `balance` and `lines` from the existing `payment.posted` read model. It additionally calls `ledger.balance` for `availableCents`. With a new ledger it reads the integer `balanceCents` field; with an old ledger it converts the legacy decimal `balance` field to minor units. Payment events and the persisted customer read model are unchanged, so old and new customer instances can share the database and consume retained events.

## Rollback

Stop or replace new customer instances with the previous customer version independently. The old version ignores the additive `availableCents` response field and continues using the same statement tables and events. Retained events and database rows require no rollback migration.
