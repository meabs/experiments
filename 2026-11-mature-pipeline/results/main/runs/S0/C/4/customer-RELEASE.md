# Customer release

## Rollout order

There is no dependency constraint for this change. The release pipeline may use its normal order (alphabetical when no other service constraint applies) and deploy customer one instance at a time. Customer does not need to be atomic with decision or wait for queued events to drain.

## Mixed-version behaviour

The new customer calls `decision.score` as before and always uses `score` to calculate `decision`. If the decision response contains `reason`, customer copies it to the `apply` response; if it does not, customer omits the field. Therefore a new customer instance works with an old decision instance, and an old customer instance works with a new decision instance because the added decision field is ignored. No database migration or event-format change is involved.

## Rollback

If the rollout fails, stop and route traffic back to the previous customer version, one instance at a time. The previous version remains compatible with both decision response shapes, so rollback does not require reverting data, draining queues, or changing decision instances. Any already-served `reason` field simply disappears when the old customer handles later requests.
