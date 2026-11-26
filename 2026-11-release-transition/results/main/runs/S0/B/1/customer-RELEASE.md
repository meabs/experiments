# Customer release plan

## Rollout order

No service dependency constrains this release. Deploy `customer` independently, one instance at a time, using the normal rollout order (with no required `deploy_after`, `atomic_with`, or queue drain). The `decision` service may be deployed before, during, or after this rollout.

## Mixed-version behavior

The new customer accepts both the existing `decision.score` response (`score`) and the additive response containing `reason`. It returns `decision` and `score` as before and includes `reason` only when the decision response supplies it. During a mixed rollout, old customer instances continue to work with either decision version and omit the new field; new customer instances work with the old decision version and also omit it. The change does not alter databases, queued events, or event handling.

## Rollback

If the rollout fails, stop it and route traffic back to the remaining old customer instances or redeploy the old customer version one instance at a time. No data migration or queued-event cleanup is needed. Any `reason` fields returned by new customer instances disappear when traffic is rolled back to old instances; the existing `decision` and `score` fields remain compatible throughout.
