# Customer release

## Rollout order

No dependency or atomic switch is required. Use the normal alphabetical rollout, one instance at a time. Customer may therefore roll out before or after `decision`.

## Mixed-version behavior

New customer instances accept both the current `decision.score` response and the additive response containing `reason`; they include `reason` in `apply` only when it is present. Old customer instances ignore the extra field from new decision instances. Thus old and new customer and decision instances can serve traffic together, and queued data needs no migration.

## Rollback

Rollback customer instances one at a time to the previous version. The previous customer version continues to work with either decision response because it already ignores unknown response fields. No database or queued-event rollback is needed: this change adds no schema or event changes.
