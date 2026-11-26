# Customer release

## Rollout order

Deploy all customer instances first, one instance at a time, and verify them
before allowing the ledger rollout to start. The ledger release should enforce
this dependency with `deploy_after: ["customer"]`. `drain_before` is enabled
for this service so payment events already queued before the customer rollout
are processed before deployment.

## Mixed-version behaviour

The new customer consumes ledger's `payment.posted` events using `amountMinor`
and retains a fallback for the legacy decimal `amount`. This allows new
customer instances to process both old queued events and new events while
customer instances are being replaced. The existing statement table remains
in minor units, so balances and line counts are unchanged.

Ledger must not switch to amountMinor-only events until every customer
instance is new: an old customer instance cannot process that event shape.

## Rollback

Before rolling customer back after ledger has switched, roll ledger back to the
old event producer, then drain `payment.posted` events. Only after that drain
is it safe to replace customer instances with the old version. If customer
rollout fails before ledger switches, stop and roll back customer normally;
legacy ledger events remain supported. Do not roll back customer first after
the ledger switch, because the old customer cannot read amountMinor-only
events.
