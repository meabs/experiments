# Customer release

## Rollout order

Customer has no deployment dependency on decision for this change. It may be rolled out one instance at a time using the pipeline's normal order (alphabetical when no other service adds a constraint). No atomic switch or event drain is required.

## Mixed-version behavior

The new customer version copies `reason` from `decision.score` when that field is present and otherwise returns the existing `decision` and `score` fields. Therefore, a new customer instance works with the old decision version, which returns only `score`. An old customer instance ignores the additional `reason` returned by a new decision version. Existing databases and queued events are unchanged.

## Rollback

If the rollout fails, stop and roll back customer instances individually to the previous version. The previous version remains compatible with either decision version because it does not require `reason`. No database migration or queued-event replay is needed; preserve the shared database and event contents.
