# Customer release

## Rollout order

No cross-service ordering or atomic switch is required. With no constraints, the pipeline's default alphabetical order deploys customer before decision, one instance at a time; either service may also be rolled out independently.

## Mixed versions

The new customer version always sends and uses the existing `score` field. It copies `reason` only when decision returns it, so it works with the old decision version. The old customer version ignores an additive `reason` field from a new decision version. Existing queued events and database contents are unchanged.

## Rollback

Roll back customer one instance at a time if needed. The previous customer version remains compatible with both decision response shapes, and no data migration or queue rewrite is required.
