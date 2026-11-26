# Customer release

## Rollout order

Deploy customer independently, one instance at a time. There is no required ordering relative to decision and no need for an atomic switch. The normal pipeline order is therefore acceptable.

## Mixed-version behavior

The new customer version always returns `decision` and `score` as before, and additionally returns `reason` only when `decision.score` supplies it. It works with old decision instances, which omit `reason`. Old customer instances ignore the extra field from new decision instances, so either service can be rolled out first and old and new instances can serve traffic together.

There are no schema, event, or queued-message changes in this release.

## Rollback

If the rollout fails, stop and roll back customer instances to the previous version one at a time. The previous version remains compatible with both decision response shapes. No database migration or event cleanup is required; already returned responses are not persisted.
