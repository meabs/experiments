# Customer release

## Rollout order

No dependency constraint is required. Deploy customer instances one at a time in the pipeline's normal order; ledger may be fully old, fully new, or in a mixed rollout while customer is changing. Ledger does not need to be drained first.

## Mixed-version behaviour

The new customer version calls `ledger.balance` for `statement`. It prefers the new additive `balanceCents` field and converts the legacy decimal `balance` field when talking to an old ledger instance. It also consumes either the existing decimal `amount` field or the additive `amountCents` field on `payment.posted`, so queued events remain usable across the rollout. Old customer instances do not require the new field and continue to operate with either ledger version.

The existing customer statement read model and queued events are retained. `availableCents` reflects the synchronous ledger response; `balance` and `lines` remain the event-backed read model.

## Rollback

If the rollout is rolled back, route traffic back to old customer instances one at a time. They ignore `availableCents` and continue using the event-backed statement response; no database migration or event rewrite is needed. Leave queued events and the shared database in place. A later retry of the rollout can consume the same compatible event formats.
