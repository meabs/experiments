# Ledger release

## Rollout order

Deploy the customer change completely before deploying ledger. The pipeline may still roll out each service one instance at a time, but no ledger instance using the new event format should be started until every customer instance is on the compatible version.

## Mixed-version behavior

During the customer rollout, old ledger instances continue publishing the legacy decimal `amount` event, so the new customer must continue accepting that format while it is being rolled out. Once customer is fully deployed, new ledger instances publish `payment.posted` with `amountMinor` (an integer pence value encoded as a string) and no `amount` field. The customer read model should consume both formats so queued legacy events remain processable.

## Rollback

If ledger must be rolled back, leave the upgraded customer deployed, roll ledger instances back one at a time, and allow the resulting legacy `amount` events to be processed. Drain the event queue before reverting customer; reverting customer while `amountMinor` events remain queued is not safe. If customer rollback is required, do it only after that drain and with the ledger already on the old version.
