# CHG-101 rollout

## Rollout order

Prepare the new `ledger` and `customer` versions, including the customer's compatibility handling for queued legacy events, then switch both services atomically. All instances switch together and no traffic is sent to a mixed-version pair. There is no drain requirement: queued events are retained and the new customer must process both the pre-switch decimal event shape and the new `amountMinor` shape.

## Mixed-version behavior

The ledger database and event queue are shared across versions. The ledger keeps its existing posting table and synchronous `post`, `balance`, and `postings` contracts unchanged. The new ledger publishes `payment.posted.amountMinor` as a pence integer string and no longer publishes the decimal `amount` field. Because old customer instances cannot consume that event shape, the atomic switch prevents ledger-new/customer-old traffic. Before the switch, old ledger events may remain queued; customer-new must consume those safely.

## Rollback

If preparation or health checks fail before the switch, leave both old versions serving. If the switched release must be rolled back, switch `ledger` and `customer` back together, with no ledger-only rollback. This preserves event compatibility: old ledger emits the legacy decimal event shape, which the old customer understands. Keep the shared database and queued events; do not delete or replay postings as part of rollback. Any events emitted by the new ledger before rollback must be drained or otherwise handled by the compatible customer version before old customer traffic resumes.
