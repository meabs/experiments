# Decision rollout

## Order

There is no required deployment order and no atomic switch. Deploy decision one instance at a time using the normal alphabetical pipeline order, with health checks between instances. Do not wait for queued events: decision is stateless and does not consume or produce events.

## Mixed versions

The new `score` response is additive: it retains `score` and adds `reason`. Old customer instances only use `score`, so they work with both old and new decision instances. The CHG-100 customer version must treat a missing `reason` as a valid response while old decision instances remain, so it also works with both versions. No database or queue migration is involved.

## Rollback

If rollout fails, stop and route traffic back to the previous decision instances, or redeploy the previous decision artifact one instance at a time. Both versions have the same request and `score` contract; rolling back only removes the optional `reason` field. No data or queued events need to be reverted.
