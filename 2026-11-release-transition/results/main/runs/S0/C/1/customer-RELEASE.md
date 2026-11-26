# Customer release

## Rollout order

Use the pipeline default: deploy services alphabetically, one instance at a time. Customer has no dependency that requires waiting for decision, and the two services do not need an atomic switch or an event drain.

## Mixed-version behaviour

The new customer service still sends the existing `income` and `amount` request to `decision.score` and always returns the existing `decision` and `score` fields. It adds `reason` only when the decision response includes a non-null value, so it remains compatible with the old decision service.

If the new decision service is deployed first, its additional optional `reason` field is ignored by old customer instances. If the new customer service is deployed first, old decision responses simply produce an `apply` response without `reason`.

## Rollback

Rollback customer instances independently, one at a time, if needed. The old customer version can read responses from the new decision version because the new field is optional and additive. The new customer version can read responses from the old decision version because it omits `reason` when absent. No database migration or queued-event format change is involved, so persistent data and queued events remain usable during rollback.
