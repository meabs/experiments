# Customer release

## Rollout order

Deploy customer instances one at a time in the normal pipeline order. No ledger deployment, queue drain, or atomic switch is required. The customer release can overlap the ledger rollout because it understands both ledger balance response formats.

## Mixed versions

New customer instances call `ledger.balance` and prefer the additive `balanceCents` field. If an old ledger instance responds with the existing decimal `balance` field, the customer converts it exactly to integer minor units. The existing `balance` and `lines` statement fields and the event-driven read model remain unchanged, so old and new customer instances can serve the same traffic and share the existing database.

## Rollback

If the rollout fails, stop deploying and route traffic back to the old customer instances. They continue to use the existing statement behavior; no customer schema migration or queued-event change is required. A new customer instance can also remain alongside an old ledger instance because of the decimal fallback. If ledger is rolled back, keep the new customer version deployed or roll it back independently; either choice remains compatible with the persisted database and events.
