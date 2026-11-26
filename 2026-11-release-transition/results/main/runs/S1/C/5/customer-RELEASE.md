# Customer release

## Rollout order

Roll out the new customer version to every instance first, one instance at a
time. Only after all customer instances are running this version may the ledger
roll out its `payment.posted` change to `amountMinor`. No queue drain or atomic
switch is required.

## Mixed-version behavior

The new customer reads `amountMinor` as an integer number of minor units and
updates the statement balance in integer cents. It also accepts the retired
decimal `amount` field, so events emitted by old ledger instances and events
already queued before the ledger rollout remain readable. New ledger events
must not be enabled while any old customer instance is serving traffic, because
old customer code cannot read `amountMinor`.

## Rollback

If the ledger rollout fails, stop or roll back the ledger to the old event
format before rolling any customer instance back. The new customer can safely
process either event format. If customer rollout itself fails, leave the new
instances in place or roll them back while the ledger remains on its old
format; do not expose `amountMinor`-only events until customer is fully new
again. Existing statement rows and queued events are retained across rollback.
