# Customer release

## Rollout order

Switch `customer` and `decision` atomically, with all instances changed together and no traffic between the old and new versions. The atomic constraint in `plan.json` is required because the published `score` field changes from a 0–100 scale to a 0–1000 scale; deploying either service independently would make the old customer thresholds or the new customer thresholds incorrect.

## Mixed-version behavior

There is no customer/decision mixed-version traffic during this release. The new customer calls the existing `decision.score` operation and keeps the score string in its response, while applying the new thresholds: 600+ approves, 400–599 refers, and below 400 declines. Other customer operations and persisted data are unchanged. If an operational environment cannot honor the atomic constraint, do not start this release.

## Rollback

If the release fails, stop traffic to the release cohort and atomically restore both services to their previous versions, again with no traffic between versions. Databases and queued events are retained; no customer schema migration or event-shape change is introduced, so the restored versions can continue using the existing state. Do not roll back only one of the two services.
