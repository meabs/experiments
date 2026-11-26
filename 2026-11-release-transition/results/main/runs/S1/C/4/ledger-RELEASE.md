# Release plan

## Rollout order

Deploy `ledger` and `customer` as one atomic release. All instances of both
services are switched together, with no traffic between the old and new
versions. There is no independent ordering within the pair.

## Mixed-version and event behaviour

The new ledger publishes `payment.posted` with `account`, `amountMinor`, and
`requestId`; `amountMinor` is an integer minor-unit value represented as a
string. The synchronous ledger operations and the existing postings database
are unchanged. The coordinated customer version consumes this new field and
must also tolerate already-queued legacy events containing the old decimal
`amount` field, since queued events survive deployment. The old ledger and old
customer remain together until the atomic switch, so no live mixed pair is
served.

## Rollback

If any instance fails, keep the pair on the old versions or switch all ledger
and customer instances back together. Do not roll back only one service: an
old customer cannot consume new-only events, and a new customer must continue
to handle legacy events already in the queue. The shared ledger database is
left in place; no schema rollback is required. Events already queued are
preserved and must be consumed by the version that understands their payload.
