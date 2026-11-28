# Release plan

Deploy `customer` and `ledger` as one atomic release group. Switch all instances
together, with no traffic between the old and new groups. This is required because
the new ledger publishes `payment.posted.amountMinor`, while an old customer only
understands the retired decimal `amount` field.

The new customer accepts both formats: it uses `amountMinor` when present and
falls back to legacy `amount` when replaying events already queued before the
cutover. Therefore old-format events remain safe during the transition, and the
statement read model continues to accumulate minor units correctly.

If the release fails, switch both services back together. Keep the database and
queued events intact; the old ledger/customer pair can continue with legacy events.
Do not roll back only one service, since that would expose the old customer to
amountMinor-only events (or the new customer to no new-format producer).
