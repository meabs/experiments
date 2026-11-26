# Customer release

## Rollout order

Customer imposes no ordering, atomic, or queue-drain requirement. The release
pipeline may deploy it one instance at a time wherever its combined constraints
place it. If no other service adds a constraint, the default alphabetical order
places `ledger` before `customer`.

## Mixed versions

The new customer reads `amountMinor`, the integer minor-unit value emitted by the
new ledger. It also accepts the legacy decimal `amount` emitted by old ledger
instances and by older queued events. Therefore old and new ledger/customer
instances can run together, and events retained across deployment boundaries are
processed without changing the statement balance representation.

## Rollback

Stop the rollout and route traffic back to the old customer instances. The old
customer can process events from old ledger instances; if new-ledger events are
still queued, drain or replay them only after restoring a compatible customer
version (or retain the new customer until those events are processed). No schema
rollback is required because the statement table remains unchanged.
