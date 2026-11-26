# Decision release

## Rollout order

Deploy `decision` one instance at a time using the normal alphabetical service rollout. There is no dependency requiring `customer` to be fully deployed first, and this change does not require an atomic switch or an event drain.

## Mixed-version behavior

The new `decision.score` response adds `reason` while retaining `score`. Old decision instances return only `score`; new instances return both. Existing and new customer instances must accept either response: `score` remains the decision input, and `reason` is optional until the customer change is deployed. No database or queued-event migration is involved.

## Rollback

If the rollout fails, stop it and route traffic back to the old decision version (or redeploy the old artifact) one instance at a time. The old version remains compatible because callers continue to receive `score`; any customer behavior that uses `reason` must treat its absence as unavailable until the decision rollout is restored.
