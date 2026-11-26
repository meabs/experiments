# Customer release: CHG-101 compatibility

## Rollout order

1. Roll out this customer version one instance at a time until every customer
   instance is new.
2. Only after that, roll out the ledger CHG-101 version one instance at a time.

The customer constraint is intentionally non-atomic: the customer is backward
compatible with the old ledger, and the ledger team must sequence its release
after customer is fully deployed. No queue drain is required.

## Mixed-version behaviour

New customer instances prefer `payment.posted.amountMinor`, which is an integer
minor-unit value, and fall back to the legacy decimal `amount` field. Old and
new customer instances therefore both process events from old ledger instances
during the customer rollout. Once ledger is upgraded, old customer instances
must no longer receive minor-unit-only events; that is why ledger follows the
completed customer rollout.

The statement table continues to store `balance_cents`, so existing statements
and queued events remain usable without a data migration.

## Rollback

If the customer rollout fails, stop it and route traffic back to old customer
instances; they remain compatible with the old ledger event format. If ledger
has not yet started, no further coordination is needed.

If the ledger rollout fails after customer is complete, roll ledger back to its
old version. The new customer continues to accept the legacy decimal events.
Do not roll customer back while the new ledger is emitting amountMinor-only
events; first roll ledger back (or complete deployment of the new customer)
before any old customer instance receives those events.
