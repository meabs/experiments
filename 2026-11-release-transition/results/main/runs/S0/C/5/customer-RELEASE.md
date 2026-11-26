# Customer release plan

## Rollout order

Use the normal independent rollout, one instance at a time, in alphabetical service order. No `deploy_after`, `atomic_with`, or `drain_before` constraint is needed for customer.

## Mixed-version behaviour

The new customer accepts the existing decision response containing `score` and also accepts the additive `reason` field. It returns `reason` only when decision supplies it, so the legacy response shape is preserved for legacy decision instances. The old customer ignores the extra `reason` field from a new decision instance. Therefore either service can be upgraded first and traffic can be served by old and new instances during the rollout.

The customer database schema and queued events are unchanged, so the rollout does not require draining events or a data migration.

## Rollback

If the customer rollout fails, stop replacing instances and route traffic back to the previous customer version. The previous version remains compatible with both old and new decision versions because it ignores the optional `reason`. Any new customer instances can be replaced independently; no database or queued-event rollback is required.
