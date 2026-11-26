# Customer release

## Rollout order

Deploy customer instances in the pipeline's normal alphabetical rolling order, one instance at a time. No `deploy_after`, `atomic_with`, or `drain_before` constraint is needed for this additive contract change.

## Mixed versions

While old and new customer instances run together, both call the existing `decision.score` operation. A new customer instance accepts the old decision response containing only `score`, and returns the legacy `apply` shape. When a new decision instance also supplies `reason`, the new customer instance includes it in `apply`; old customer instances continue returning their legacy shape and ignore the extra field from decision.

The customer change does not alter stored data, queued events, or event schemas.

## Rollback

If the rollout fails, stop it and roll customer instances back individually to the previous version. The previous version remains compatible with both old and new decision responses, so no coordinated rollback or data migration is required. Any already-returned optional `reason` fields may disappear after rollback, which is an expected version-dependent response shape.
