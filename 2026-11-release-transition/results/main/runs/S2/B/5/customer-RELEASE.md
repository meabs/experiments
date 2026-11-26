# Customer rollout

## Order

There are no cross-service ordering or atomic-switch constraints. Use the normal
one-instance-at-a-time rollout; with no constraints, the pipeline's default
alphabetical order applies. Customer may therefore be deployed before or after
ledger CHG-102.

## Mixed versions

The new customer calls `ledger.balance` for `statement` and prefers the new
`balanceCents` field. While an old ledger instance is still serving traffic, it
falls back to that instance's legacy decimal `balance` field and converts it to
minor units. A new ledger can serve old customer instances because old customer
does not depend on the added response field. Existing `payment.posted` events
and the customer statement read model remain unchanged.

## Rollback

Rollback customer one instance at a time using the existing database and event
queue. The old customer continues to consume the unchanged payment events; the
new `availableCents` response is simply absent until the new customer is
redeployed. No schema migration or queue drain is required. If ledger is rolled
back independently, the customer fallback to decimal `balance` continues to
work.
