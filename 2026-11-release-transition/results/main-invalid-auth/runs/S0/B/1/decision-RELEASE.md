# Decision release

## Rollout order

Roll out `decision` one instance at a time and finish all decision instances before starting the CHG-100 `customer` rollout. The customer release should declare `deploy_after: ["decision"]` so the pipeline enforces that order; no atomic deployment or event drain is required.

## Mixed-version behavior

The new `decision.score` response adds `reason` and keeps the existing `score` unchanged. Old customer instances ignore the additional field, while new customer instances can read it. Old decision instances remain callable by either customer version because they continue to accept the same request. The service is stateless, so no database or queued-event migration is needed.

## Rollback

If the decision rollout fails, stop it and route traffic back to the old decision instances; there is no state to undo. If customer rollout has not started, this is immediately safe. If customer rollout is in progress, roll customer instances back independently while retaining the old/new decision compatibility; do not remove the new decision instances until any new customer instances have been rolled back or confirmed no longer depend on `reason`.
