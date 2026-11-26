# Decision release

## Rollout order

Switch `decision` and `customer` together, with all instances changed before traffic is admitted. The `atomic_with` constraint prevents a new customer instance from calling an old decision instance that does not return `reason`. There is no queued state or event stream in `decision`, so no drain is required.

## Mixed-version behaviour

The new `decision.score` response adds `reason` while retaining the existing `score` field and its meaning. Old customer instances ignore the extra field and continue to work. During the constrained switch, old versions may remain available for rollback, but traffic is not sent to a new customer paired with an old decision.

## Rollback

If the switch fails, route traffic back to the old versions of both services together. The old contract remains valid for old customer instances. Because the change is stateless and adds no database or event data, no data rollback or queue replay is required.
