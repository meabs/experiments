# Release plan

## Rollout order

`decision` and `customer` are one atomic release unit for CHG-100. Deploy the new artifacts to all instances, but switch all instances of both services together with no traffic between the old and new versions. There is no required database migration or event-queue drain for this change.

## Mixed-version behavior

The new decision version keeps the existing `score` field and adds `reason`; old customer versions ignore the additional response field. The customer change therefore must not be exposed while any old decision instance remains active, which is why the switch is atomic. The services are stateless for this feature, and no database or queued-event contents are changed.

## Rollback

If validation fails, keep traffic off the new pair and switch all decision and customer instances back to the previous artifacts together. Since the change is additive and has no schema or event changes, the retained databases and queued events require no rollback or replay. If rollback occurs after a partial deployment, discard the new instances and restore the old pair before resuming traffic.
