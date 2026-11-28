# Release rollout

Customer and ledger must be switched atomically, with all instances of both services changed together and no traffic routed between the old and new versions during the switch. No service is deployed first; this avoids exposing an old customer instance to a new ledger's `amountMinor`-only events.

The new customer sends `amountMinor` to `ledger.post` and also retains the legacy decimal `amount` field, so either ledger version can handle requests during a compatible transition. Its statement consumer reads `amountMinor` and accepts legacy `amount` events already present in the queue or database. Balances continue to be stored and returned as minor-unit cents formatted as decimal major units.

If the rollout fails, stop the switch and restore the old customer and ledger versions together, again before routing traffic. The old pair can process old decimal events; do not roll back customer alone after the new ledger has emitted `amountMinor` events. Existing data and queued events are preserved, and a later retry of the atomic switch can process them with the new customer.
