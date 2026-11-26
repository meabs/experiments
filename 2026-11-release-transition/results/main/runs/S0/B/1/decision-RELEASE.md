# Decision release

## Rollout order

Deploy the new decision version to all instances, one instance at a time, and verify health before proceeding. Complete decision before deploying the coordinated customer change. No atomic cutover or queued-event drain is required because decision is stateless and synchronous.

## Mixed-version behaviour

The new `score` operation accepts the existing `{income, amount}` request and returns the existing `score` plus the additive `reason` field. Old customer instances ignore the extra field and continue using `score`, so old and new decision instances can serve traffic together. The customer rollout must follow decision: a new customer instance requires `reason`, which an old decision instance does not return.

## Rollback

If the decision rollout fails, stop and route traffic back to the old decision version; no database or event rollback is needed. If customer has not started, the old customer version remains compatible. If customer has started, roll back customer first (new customer must not call old decision), then roll back decision. Since decision is stateless, switching versions does not discard persistent state.
