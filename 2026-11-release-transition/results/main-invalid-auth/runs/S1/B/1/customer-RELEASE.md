# Customer release plan

## Rollout order

Deploy the new customer version to every instance first, one instance at a
time. Once all customer instances are healthy, deploy the CHG-101 ledger
version one instance at a time. The ledger rollout must therefore include a
dependency on customer being fully deployed before ledger starts.

No queue drain or atomic switch is required: customer can process both event
formats while the estate transitions.

## Mixed-version behaviour

The new customer reads `amountMinor` from new `payment.posted` events and falls
back to legacy decimal `amount` for events already queued or emitted by an old
ledger. This keeps statement balances correct while old and new ledger
instances coexist. The new ledger must not be introduced while any old
customer instance remains, because the old customer only understands
`amount`.

## Rollback

If the customer rollout fails, stop it and roll back customer instances; the
old ledger remains safe because it emits legacy `amount` events. If the ledger
rollout fails, roll back ledger instances to the old version; the new customer
continues to accept those legacy events. Preserve the database and queued
events in either case; do not replay a posting as a new request.
