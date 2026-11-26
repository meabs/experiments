# Decision rollout

## Order

No cross-service ordering or atomic switch is required. The release pipeline may use its default alphabetical, one-instance-at-a-time rollout. There are no queued events or database migrations for this stateless change.

## Mixed versions

The new `score` response keeps `score` unchanged and adds `reason` as an optional additive field. Old decision instances omit it; new decision instances return it. Old customer instances ignore the extra field, so customer and decision can be mixed during rollout. New customer instances can read `reason` when calling either a new decision instance or, while a rollback is in progress, an old one; customer should treat a missing reason as absent rather than as a failed call.

## Rollback

Roll back decision instances one at a time. Existing requests and old customer instances continue to work because `score` is unchanged. If the new customer version has to be rolled back too, roll customer back first (or together with decision) before rolling decision back, so no new customer instance depends on a field that old decision instances do not provide. No data or queued events need to be reverted.
