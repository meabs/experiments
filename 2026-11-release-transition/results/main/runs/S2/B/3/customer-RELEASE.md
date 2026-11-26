# Customer release

## Rollout order

Customer has no dependency requiring a special order or atomic cutover. It may be rolled out one instance at a time; with no other constraints the pipeline's normal alphabetical order is used. Ledger may therefore be old or new during the customer rollout.

## Mixed versions

The new customer calls `ledger.balance` for `statement` and prefers the additive `balanceCents` field. While old ledger instances are serving requests, it converts their legacy decimal `balance` field to minor units. New ledger instances can serve old customer instances because the old customer ignores the additional response field. Existing statement event processing and the legacy `balance` and `lines` fields remain unchanged.

## Rollback

Rollback the customer instances independently, one at a time. The old customer remains compatible with both ledger versions, and the new customer remains compatible with the old ledger, so no traffic switch or database rollback is required. Retained statement data and queued events remain usable; replaying retained payment events preserves the existing read model.
