# Customer release

## Rollout order

Customer has no dependency on the decision rollout for this change. It can follow the pipeline's normal alphabetical, one-instance-at-a-time order; there is no need for an atomic switch or an event drain. The decision service may therefore be rolled out before, during, or after customer.

## Mixed-version behavior

New customer instances accept both the existing decision response (`score`) and the additive response (`score` plus optional `reason`). They return `decision` and `score` as before, and include `reason` only when decision supplies it. Old customer instances ignore the new field because they already use only `score`, so traffic can be split between old and new instances while either decision version is live.

There are no database migrations, event changes, or new required request fields.

## Rollback

If the rollout fails, stop it and route traffic back to the old customer instances. They remain compatible with both decision response shapes, so decision does not need to be rolled back with customer. Because this release changes no persistent schema or queued event payload, rollback does not require data cleanup or event replay.
