# Customer release

## Rollout order

No cross-service ordering or atomic switch is required. Deploy customer using the normal one-instance-at-a-time rollout (with no release constraint, the pipeline's default alphabetical order applies). Ledger may still have old and new instances when customer instances are upgraded.

## Mixed-version behavior

The new customer calls `ledger.balance` for every `statement`. It uses `balanceCents` when returned by the new ledger and converts the legacy decimal `balance` response when talking to an old ledger instance. The statement's existing `balance` and `lines` fields continue to come from the customer read model, and `availableCents` is added without changing existing fields. Old customer instances ignore the additional response field and continue to operate with either ledger version.

Queued `payment.posted` events and the customer statement table require no migration. Both legacy decimal event amounts and integer `amountCents` event amounts are supported, so events produced before, during, or after the rollout can be consumed.

## Rollback

If the customer rollout is rolled back, stop upgrading instances and replace upgraded instances with the previous customer version one at a time. No database or queue cleanup is needed: the added response field is not persisted, and old customer instances continue to consume the retained events. Ledger can remain on either version; old customer instances do not depend on `balanceCents`.
