# Customer release

## Rollout order

Deploy all customer instances first, one at a time. Only after the customer
deployment is complete should ledger instances switch to the `amountMinor`
event format. The default alphabetical service order (`customer` before
`ledger`) satisfies this ordering; the ledger release must preserve it too.

## Mixed-version behaviour

The new customer reads `amountMinor` and converts it directly to the existing
minor-unit statement balance. It also reads the legacy decimal `amount` field,
so it works with old ledger instances and with events already queued before the
ledger rollout. Old and new customer instances can therefore run together
while ledger is still on its old version.

## Rollback

If the ledger rollout fails, roll ledger back first. The new customer accepts
the legacy events produced by the rolled-back ledger. Keep the new customer
version in service until all ledger instances are back on the legacy producer
and queued `amountMinor` events have been handled; only then may customer be
rolled back. Never expose an old customer instance to new ledger events, since
the old customer only understands the retired `amount` field.
