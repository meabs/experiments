# Customer release

## Rollout order

Deploy all customer instances first, one at a time, and verify that the new
version is healthy before allowing the ledger rollout to switch to
`amountMinor`-only events. No queue drain is required: the customer consumer
handles both event shapes.

## Mixed-version behavior

The new customer reads `amountMinor` as the authoritative integer number of
minor units. If it is absent, it converts the legacy decimal `amount` value to
minor units. Therefore old ledger events already in the queue, new ledger
events, old customer instances, and new customer instances can overlap while
customer is being rolled out. The statement table remains integer-based, so
balances do not depend on decimal floating-point arithmetic.

## Rollback

If customer must be rolled back before ledger changes, stop the customer
rollout and route traffic to the old customer version; both versions can read
legacy events. After ledger has switched to amountMinor-only events, roll the
ledger back first (or otherwise restore legacy event emission) before routing
events to old customer instances. Then roll customer back one instance at a
time and verify statement balances. Do not roll back customer alone while
amountMinor-only events may still be delivered.
