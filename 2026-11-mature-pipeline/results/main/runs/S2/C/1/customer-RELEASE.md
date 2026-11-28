# Customer release

## Rollout order

Deploy customer independently, one instance at a time, with no dependency on a fully deployed ledger. The default estate order may therefore be used. The ledger change may be rolled out before, during, or after customer; no atomic switch or event drain is required.

## Mixed-version behaviour

The new customer keeps the existing `balance` and `lines` statement fields and adds `availableCents`. It reads `balanceCents` when supplied by the new ledger and falls back to the legacy decimal `balance` response, so either ledger version can serve it. Its payment-event reader accepts both the existing decimal `amount` and the additive integer `amountCents` form. The ledger rollout must retain the legacy response/event fields until old customer instances are gone; the new customer does not change the shared schema.

## Rollback

Stop the new customer instances and restore the previous customer version one instance at a time. Existing customer tables and queued events remain usable, because no migration or destructive data change was made. The old version ignores the additional `availableCents` response behaviour and continues consuming the legacy ledger-compatible event fields. If ledger is rolled back independently, the new customer falls back to its decimal `balance` response.
